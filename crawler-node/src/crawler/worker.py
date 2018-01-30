#!/usr/bin/env python
import datetime
import concurrent.futures
import os
import sys
import signal
import time
import random
from contextlib import contextmanager
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import dateutil.parser
import boto3
import requests
import redis
import pytz
from elasticsearch import Elasticsearch, helpers

from crawler.loggers import logger
from crawler.conf import settings
from crawler.monitoring import scl, statsd_timer
from crawler.parser import WebsiteParser

HEADERS = {
    'Accept': 'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;',
    'Accept-Encoding': 'gzip,deflate',
    'Cache-Control': 'max-age=0',
    'User-Agent': "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:54.0) https://github.com/AusDTO/disco_crawl",
}

es = Elasticsearch(
    hosts=[settings.ANALYTICS_ES_ENDPOINT],
)

redis_client = redis.StrictRedis(
    host=settings.REDIS_LOCK_ENDPOINT,
    port=6379,
    db=settings.REDIS_LOCK_DB,
    password=settings.REDIS_LOCK_PASSWORD,
)


@statsd_timer('crawler.proc.put_to_redis')
def put_to_redis(action, domain_name):
    assert action in ('SEEN', 'FINISHED')
    # print("REDIS {} {}".format(action, domain_name))
    cli = redis.StrictRedis(
        host=settings.get('REDIS_{}_ENDPOINT'.format(action)),
        port=6379,
        db=settings.get('REDIS_{}_DB'.format(action)),
        password=settings.get('REDIS_{}_PASSWORD'.format(action)),
    )
    cli.set(
        domain_name,
        utcnow().isoformat()
    )


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]


def get_memory_usage():
    import os

    def _VmB(VmKey):
        _proc_status = '/proc/%d/status' % os.getpid()
        _scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
                  'KB': 1024.0, 'MB': 1024.0*1024.0}
        try:
            t = open(_proc_status)
            v = t.read()
            t.close()
        except Exception as e:
            logger.exception(e)
            return 0.0  # non-Linux?
        # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
        i = v.index(VmKey)
        v = v[i:].split(None, 3)  # whitespace
        if len(v) < 3:
            return 0.0  # invalid format?
        return float(v[1]) * _scale[v[2]]

    return round(_VmB('VmSize:') / 1024.0 / 1024.0)


def robots_allow(domain_name, robots, url):
    if robots and not robots.can_fetch("disco_crawl", url):
        # print("[%s] robots.txt deny %s" % (domain_name, url))
        return False
    return True


def domainize_link(domain_name, link, scheme='http'):
    parsed = urlparse(link)
    nohost = parsed._replace(scheme=scheme, netloc=domain_name)
    return nohost.geturl() or '/'


class TimeoutException(Exception):
    pass


class BlacklistManagerClass(object):
    def __init__(self):
        self.blacklist = set()

    def _get_clean_link(self, link):
        parsed = urlparse(link)
        nohost = parsed._replace(scheme='', netloc='')
        return nohost.geturl() or '/'

    def put(self, link):
        # urlparse("https://wow.xxx/a/b/c/?d=e&f=g#123")
        # ParseResult(scheme='https', netloc='wow.xxx', path='/a/b/c/', params='', query='d=e&f=g', fragment='123')
        self.blacklist.add(self._get_clean_link(link))

    def is_blacklisted(self, link):
        result = self._get_clean_link(link) in self.blacklist
        return result


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def normalize_href(href, page_url=None):
    if not href:
        return href
    # if href.startswith('../'):
    #     href = '/' + href
    parsed = urlparse(href)

    only_path = parsed.path
    if not parsed.netloc:
        # local url
        if not only_path.startswith('/') and page_url:
            # relative url
            base_directory = os.path.dirname(page_url.path)
            if not base_directory.endswith('/'):
                base_directory += '/'
            only_path = base_directory + only_path

    norm_path = os.path.normpath(only_path)
    if only_path.endswith('/') and not norm_path.endswith('/'):
        norm_path += '/'
    normalized_parsed = parsed._replace(path=norm_path)
    if normalized_parsed.path == '.':
        # root domain
        normalized_parsed = normalized_parsed._replace(path='')
    if normalized_parsed.path.endswith('/.'):
        normalized_parsed = normalized_parsed._replace(path=normalized_parsed.path[:-1])
    if '..' in href:
        print("Normalize url {} @ {} to {}".format(page_url, href, normalized_parsed.geturl()))
    if normalized_parsed.fragment:
        # print("Remove fragment from the url {}".format(normalized_parsed))
        normalized_parsed = normalized_parsed._replace(fragment=None)
    return normalized_parsed.geturl()


class LinkParser(HTMLParser):
    def __init__(self, page_url, *args, **kwargs):
        self.links = set()
        self.page_url = urlparse(page_url)
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        # Only parse the 'anchor' tag.
        if tag == "a":
            # Check the list of defined attributes.
            attrs = dict(attrs)
            href = (attrs.get('href', '') or '').strip()
            rel = (attrs.get('rel', '') or '').lower().strip()
            if href.startswith('#'):
                # internal in-page or complex javascript link, ignore
                return
            if rel == 'nofollow':
                return
            if href == '#' or href.lower().startswith('javascript:'):
                return
            if href.lower().startswith('mailto:'):
                return
            if href.lower().startswith('tel:'):
                return
            self.links.add(
                normalize_href(href, self.page_url).strip().replace('\n', '').replace('\r', '')
            )


def is_domain_local(our_domain, target_domain):
    if our_domain.startswith('www.'):
        pure_domain = our_domain[len('www.'):]
        www_domain = our_domain
    else:
        pure_domain = our_domain
        www_domain = 'www.' + our_domain
    if not target_domain:
        return True
    if target_domain in (pure_domain, www_domain):
        return True
    return False


@statsd_timer('crawler.proc.get_already_crawled')
def get_already_crawled(domain_name):
    already_crawled = set()
    next_links = set()

    mybl = BlacklistManagerClass()

    try:
        objects = []
        scan_iterator = helpers.scan(
            client=es,
            index=settings.ANALYTICS_ES_INDEX_NAME,
            doc_type='crawledpage',
            q='DomainName:"{}"'.format(domain_name),
            size=1000,
            scroll='2m',
        )
        for obj_found in scan_iterator:
            objects.append(obj_found['_source'])
        for hit in objects:
            link = hit['identifier']
            already_crawled.add(link)
            mybl.put(link)
        for hit in objects:
            for sublink in hit.get('links', []) or []:
                if not mybl.is_blacklisted(sublink):
                    next_links.add(sublink)
    except Exception as e:
        if 'index_not_found_exception' not in str(e):
            logger.exception(e)
    next_links = list(next_links)[:settings.MAX_RESULTS_PER_DOMAIN]
    random.shuffle(next_links)
    return list(already_crawled)[:], next_links[:]


@statsd_timer('crawler.proc.postprocess_resp')
def postprocess_resp(domain_name, scheme, url, resp, data, error, head_execution_time=None):
    scl.incr('crawler.postprocess.started')
    external_domains = set()
    internal_links = set()
    external_links = set()

    content_type = resp.headers.get('Content-Type', 'binary/octet-stream') if resp else None
    is_html = content_type.startswith('text/') if content_type else False

    print("[{}://{}] Processing {}: {} len {}, {} {}".format(
        scheme,
        domain_name,
        resp.status_code if resp else 0,
        content_type,
        'non-html' if data == '...' else error if error else len(data),
        url,
        ", {}".format(error) if error else ""
    ))

    if is_html:
        parser = LinkParser(page_url=url)
        parser.feed(data.decode('utf-8'))
        for link in parser.links:
            if not link:
                continue
            if link.startswith('mailto:') or link.startswith('tel:'):
                continue
            if link.startswith('#') or link.lower().startswith('javascript:'):
                continue
            if link.endswith('/.'):
                link = link[:-1]
            parsed_url = urlparse(link)
            if not parsed_url.scheme and parsed_url.netloc:
                parsed_url = parsed_url._replace(scheme=scheme)
            if not parsed_url.netloc or is_domain_local(domain_name, parsed_url.netloc):
                # local link
                normalized_url = parsed_url.geturl()
                internal_links.add(normalized_url)
            else:
                # external link
                external_links.add(parsed_url.geturl())
                if parsed_url.netloc != domain_name and parsed_url.netloc not in external_domains:
                    external_domains.add(parsed_url.netloc)
                    if parsed_url.netloc.endswith('.gov.au'):
                        # interesting for us
                        put_to_redis("SEEN", parsed_url.netloc)
    scl.incr('crawler.postprocess.internal-links-found', len(internal_links))
    scl.incr('crawler.postprocess.external-links-found', len(external_links))
    try:
        parser = WebsiteParser(
            is_html=is_html,
            url=url,
            body=data,
            internal_links=list(internal_links)[:],
            external_links=list(external_links)[:],
            external_domains=list(external_domains)[:],
            resp=resp,
            error=error,
            head_execution_time=head_execution_time,
        )
        parser.put_to_es()
        parser.put_to_s3()
    except Exception as e:
        logger.exception(e)
        scl.incr('crawler.postprocess.exception')
    finally:
        del parser
    scl.incr('crawler.postprocess.done')
    return list(internal_links)[:]


@statsd_timer('crawler.proc.do_work')
def do_work(domain_name, scheme, url, sleep_seconds):
    # in-thread worker which sleeps for some second and then does the crawl and processing
    if not sleep_seconds:
        sleep_seconds = settings.DOWNLOAD_DELAY
    sleep_seconds = max(sleep_seconds, settings.DOWNLOAD_DELAY) * settings.WORKERS

    url = domainize_link(domain_name, url, scheme=scheme)
    print("[{}://{}] Crawling {} with desired delay {}s".format(
        scheme, domain_name, url, sleep_seconds
    ))

    sleep_timeout = random.randint(sleep_seconds, int(sleep_seconds * 1.4))
    scl.incr('crawler.generic.slept_ms', sleep_timeout * 1000)
    time.sleep(sleep_timeout)

    resp, data, error = None, None, None

    t_before_head = time.time()
    scl.incr('crawler.domain.fetch-head')
    try:
        r_resp = requests.head(url, allow_redirects=True, headers=HEADERS, timeout=10)
        resp = r_resp
        data = '...'
    except Exception as e:
        scl.incr('crawler.domain.fetch-head-exception')
        formatted = str(e)
        # if 'ssl.CertificateError' in formatted or 'socket.gaierror' in formatted or 'httplib2.' in formatted:
        #     log the problem
        resp, data, error = None, 'error', "Can't fetch the url: {}".format(formatted)
    else:
        scl.incr('crawler.domain.fetch-head-success')
    head_execution_time = time.time() - t_before_head
    scl.timing('crawler.domain.head-execution-time', head_execution_time)

    content_type = resp.headers.get('Content-Type', 'binary/octet-stream') if resp else None
    is_html = content_type.startswith('text/') if content_type else False
    if is_html:
        scl.incr('crawler.domain.is-html')
    else:
        scl.incr('crawler.domain.is-non-html')

    if is_html:
        # worth fetching the body
        scl.incr('crawler.generic.slept_ms', sleep_seconds * 1000)
        time.sleep(sleep_seconds)
        try:
            r_resp = requests.get(
                url,
                headers=HEADERS,
                allow_redirects=True,
                timeout=10
            )
            resp = r_resp
            data = resp.content
        except Exception as e:
            scl.incr('crawler.domain.fetch-get-exception')
            # connection error most likely
            formatted = str(e)
            # if 'ssl.CertificateError' in formatted or 'socket.gaierror' in formatted or 'httplib2.' in formatted:
            # TODO: count problems to not download the website with bad certificate or down now but working
            # 5 minutes ago and so on, so stop after 20 major problems like timeout or TLS error
            #     q_problems.put(formatted)
            resp, data, error = None, 'error', formatted
            logger.error("[%s] Error %s for %s", domain_name, formatted, url)
        else:
            scl.incr('crawler.domain.fetch-get-success')
    # print(domain_name, url, resp, data, error)
    return postprocess_resp(
        domain_name, scheme, url,
        resp, data, error,
        head_execution_time=head_execution_time
    )


@statsd_timer('crawler.proc.put_message_to_es')
def put_message_to_es(domain_name, msg):
    scl.incr('es.message.pushed')
    es.index(
        index=settings.ANALYTICS_ES_CRAWLED_INDEX_NAME,
        body={
            "DomainName": domain_name,
            "{}At".format(msg): utcnow(),
            "RecentStatus": msg,
            "eventDate": utcnow(),
        },
        doc_type='domain-{}'.format(msg),
    )


def do_main_futures(domain_name):
    global redis_client

    if is_redis_crawl_locked(domain_name):
        scl.incr('crawler.domain.ratelimited')
        return False
    scl.incr('crawler.domain.started')

    blacklist = BlacklistManagerClass()
    sleep_seconds = settings.DOWNLOAD_DELAY
    robots = None
    scheme = 'http'  # by default it's http, but we try to determine if it's https

    # try to guess the http/https version
    try:
        r = requests.head('https://{}'.format(domain_name))
        str_status = str(r.status_code)
        if str_status.startswith('2') or str_status.startswith('1'):
            scheme = 'https'
        scl.incr('crawler.domain.https_found')
    except Exception as e:
        print("While trying to request https version got {} error".format(e))
        scl.incr('crawler.domain.https_not_found')

    # fetch robots.txt file
    try:
        with time_limit(30):
            robots = RobotFileParser(
                '{}://{}/robots.txt'.format(
                    scheme,
                    domain_name
                )
            )
            robots.read()
    except TimeoutException:
        logger.error(
            "[%s://%s] Timeout fetching the robots.txt file, ignoring the website",
            scheme, domain_name
        )
        scl.incr('crawler.domain.broken')
        scl.incr('crawler.domain.robots-timeout')
        put_message_to_es(domain_name, msg="broken")
        put_to_redis("FINISHED", domain_name)
        exit(10)
    except Exception as e:
        logger.error("[%s://%s] Corrupted robots.txt file: %s", scheme, domain_name, str(e))
        scl.incr('crawler.domain.robots-corrupted')
    else:
        scl.incr('crawler.domain.robots_parsed')
        try:
            if robots:
                rrate = robots.request_rate("*")
                if rrate:
                    sleep_seconds = max(rrate.seconds or settings.DOWNLOAD_DELAY, settings.DOWNLOAD_DELAY)
                    scl.incr('crawler.domain.robots_have_custom_delay')
        except Exception as e:
            pass

    if not robots or not robots.default_entry:
        scl.incr('crawler.domain.robots-invalid')
        robots = None

    # ensure it's not govCMS or apply extra limits if it is
    try:
        index_page_resp = requests.head('{}://{}'.format(scheme, domain_name))
    except Exception as e:
        print("[{}://{}] Error fetching index page, exiting".format(
            scheme,
            domain_name
        ))
        scl.incr('crawler.domain.broken')
        put_message_to_es(domain_name, msg="broken")
        put_to_redis("FINISHED", domain_name)
        return False

    is_govcms_website = 'govcms' in (index_page_resp.headers.get('X-Generator') or '').lower()
    print("[{}://{}] Website is {}a govCMS".format(
        scheme,
        domain_name,
        "" if is_govcms_website else "NOT "
    ))
    if is_govcms_website:
        scl.incr('crawler.domain.govcms')
    else:
        scl.incr('crawler.domain.non-govcms')
    if is_govcms_website and is_redis_crawl_locked('govcms'):
        scl.incr('crawler.domain.govcms-ratelimited')
        scl.incr('crawler.domain.ratelimited')
        print("[{}://{}] Overall this website is not locked, but it's govCMS, so it's locked".format(
            scheme,
            domain_name
        ))
        return False

    put_message_to_es(domain_name, msg="started")

    already_crawled, next_links = get_already_crawled(domain_name)
    if already_crawled or next_links:
        print("[{}://{}] Already {} links, {} to crawl".format(
            scheme, domain_name,
            len(already_crawled),
            len(next_links)
        ))
        scl.incr('crawler.domain.kickstart-links-alreadycrawled', len(already_crawled))
        scl.incr('crawler.domain.kickstart-links-startwith', len(next_links))
    if not next_links:
        next_links = ["{}://{}".format(scheme, domain_name)]
    for ac in already_crawled:
        blacklist.put(ac)

    this_worker_crawled_count = 0
    while True:
        new_links = []  # where to store results
        chunks_to_crawl = chunks(
            [
                normalize_href(link)
                for link
                in next_links
                if robots_allow(domain_name, robots, link)
            ],
            50  # 50 per iteration, random value in fact, just to have the ability to exit any time
        )
        for chunk in chunks_to_crawl:
            # we update it single time on each chunk (50 domains) start, because chunks
            # are rarely slower than 3-10 minutes and we lower redis load by that
            # (and the code is simpler, we don't call redis from the insides of the thread)
            redis_client.set(
                "crawled_started_{}".format('govcms' if is_govcms_website else domain_name),
                utcnow().isoformat()
            )
            memused = get_memory_usage()
            if memused > 700:
                print("[{}] Too much memory consumed ({}MB), exiting".format(
                    domain_name,
                    memused,
                ))
                this_worker_crawled_count = settings.MAX_RESULTS_PER_DOMAIN
                scl.incr('generic.script.memory-limited')
            else:
                scl.incr('crawler.links.trying', len(chunk))
                with concurrent.futures.ThreadPoolExecutor(max_workers=settings.WORKERS) as executor:
                    # Start the load operations and mark each future with its URL
                    sublinks = {
                        executor.submit(
                            do_work,
                            domain_name,
                            scheme,
                            url,
                            sleep_seconds=robots.crawl_delay(url) if robots else sleep_seconds or sleep_seconds
                        ): url
                        for url in chunk
                    }
                    for future in concurrent.futures.as_completed(sublinks):
                        url = sublinks[future]
                        try:
                            data = future.result()
                        except Exception as exc:
                            logger.exception(exc)
                            print('[{}] {} generated an exception: {}'.format(domain_name, url, exc))
                        else:
                            this_worker_crawled_count += 1
                            new_links += data
        if this_worker_crawled_count >= settings.MAX_RESULTS_PER_DOMAIN:
            print("[{}] Max crawls reached, exiting".format(domain_name))
            scl.incr('generic.script.maxcrawls-limited')
            break

        next_links = []
        new_links = set(new_links)
        for link in new_links:
            if not blacklist.is_blacklisted(link):
                blacklist.put(link)
                next_links.append(domainize_link(domain_name, link, scheme=scheme))
        if not next_links:
            scl.incr('crawler.domain.finished-completely')
            print("[{}] Nothing more to crawl".format(domain_name))
            put_message_to_es(domain_name, msg="finished")
            put_to_redis("FINISHED", domain_name)
            break
        next_links = next_links[:settings.MAX_RESULTS_PER_DOMAIN]
    scl.incr('crawler.domain.finished-iteration')
    return True


@statsd_timer('crawler.proc.is_redis_crawl_locked')
def is_redis_crawl_locked(domain_name):
    def _check_domain(domain_name):
        global redis_client
        recent_crawled_at = redis_client.get("crawled_started_{}".format(domain_name))
        if not recent_crawled_at:
            return False
        # it's been crawled some time ago, check how long
        parsed_date = dateutil.parser.parse(recent_crawled_at)
        duetime = utcnow() - datetime.timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES)
        if parsed_date:
            if parsed_date > duetime:
                print("[{}] Dropping the message, locked till {}".format(domain_name, parsed_date))
                return True
        else:
            print("[{}] Unparseable datetime".format(domain_name, recent_crawled_at))
        return False

    nowww, www = None, None
    if domain_name.startswith('www.'):
        nowww = domain_name[len('www.'):]
        www = domain_name
    else:
        nowww = domain_name
        www = 'www.' + domain_name

    # at least one variant locked - ignore it
    return _check_domain(nowww) or _check_domain(www)


@statsd_timer('crawler.proc.fetch_domain_from_sqs')
def fetch_domain_from_sqs():
    sqs_resource = boto3.resource('sqs', region_name=settings.AWS_REGION)
    requests_queue = sqs_resource.get_queue_by_name(
        QueueName=settings.QUEUE_REQUESTS.split(':')[-1],
        QueueOwnerAWSAccountId=settings.QUEUE_REQUESTS.split(':')[-2]
    )
    msgs = requests_queue.receive_messages(
        MaxNumberOfMessages=1, WaitTimeSeconds=10
    )
    if msgs:
        msg = msgs[0]
        domain_name = msg.body
        msg.delete()
        return [domain_name]
    else:
        return []


def main():
    # MODE = None
    scl.incr('generic.script.started')
    if len(sys.argv) == 2:
        # MODE = 'domain'
        logger.info("Fetching domain by name...")
        domain_name = sys.argv[1]
        do_main_futures(domain_name)
    else:
        print("Starting the crawler for SQS")
        # MODE = 'sqs'
        should_exit = False
        while not should_exit:
            # standard working cycle
            time.sleep(random.randint(1, 10))
            for domain_name in fetch_domain_from_sqs():
                crawled_something = do_main_futures(domain_name)
                if crawled_something:
                    should_exit = True
        print("Finishing the crawler")
    scl.incr('generic.script.finished')
