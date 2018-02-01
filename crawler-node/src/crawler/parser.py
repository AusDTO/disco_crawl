import base58
import datetime
import hashlib
import json
import uuid
from urllib.parse import urlparse

import boto3
import dateutil.parser
import multihash
from bs4 import BeautifulSoup

from crawler.loggers import logger
from crawler.conf import settings
from elasticsearch import Elasticsearch

es = Elasticsearch(
    hosts=[settings.ANALYTICS_ES_ENDPOINT],
)


class WebsiteParser(object):
    """
    Receive response from scrapy
    Return the list of items to save:
     * HTML content to save to S3
     * parsed dict with information to send to SQS
    """

    def __init__(self,
                 is_html,
                 url, body,
                 internal_links, external_links, external_domains,
                 resp, error=None, head_execution_time=None):
        # resp and body may be empty for binary files, in this case we just need
        # to save metadata, not content
        self.is_html = is_html
        self.url = url
        self.body = body
        self.internal_links = internal_links
        self.external_links = external_links
        self.external_domains = external_domains
        self.resp = resp
        self.error = error
        self.head_execution_time = head_execution_time

        self.domain_name = urlparse(self.url).netloc

        if self.is_html:
            self.s3_filename = self.get_s3_filename()
        else:
            self.s3_filename = None

    def get_s3_filename(self):
        return base58.b58encode(
            bytes(multihash.encode(self.body, multihash.SHA1))
        )

    def put_to_es(self):
        crawl_data = self.get_result()
        es_data = {}
        for key, value in crawl_data.items():
            if isinstance(value, dict):
                value = json.dumps(value, indent=2)
            es_data[key] = value
        es.index(
            index=settings.ANALYTICS_ES_INDEX_NAME,
            body=es_data,
            doc_type='crawledpage',
            id=hashlib.sha256(self.url.encode('utf-8')).hexdigest(),
        )

    def put_to_s3(self):
        if self.is_html and self.body:
            s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
            s3_client.put_object(
                ACL='private',
                Body=self.body,
                Bucket=settings.STORAGE_BUCKET,
                ContentEncoding='utf-8',
                ContentLength=len(self.body),
                Key=self.s3_filename,
            )

    def get_result(self):
        """
        Return parse results
        https://github.com/difchain/rmaas/blob/master/docs/WebCrawler_Client.md
        """
        soup = None
        if self.is_html:
            soup = BeautifulSoup(self.body, "lxml")
            # remove stuff
            [x.extract() for x in soup.findAll('script')]
            [x.extract() for x in soup.findAll('ul')]
            [x.extract() for x in soup.findAll('table')]
            [x.extract() for x in soup.findAll('form')]
            page_title = soup.title.text.replace('\n', '').strip() if soup.title else ''
        else:
            page_title = None

        owner = self.domain_name
        identifier = self.url

        filename = self._guess_filename(identifier)

        result = {
            'uuid': uuid.uuid4(),
            'identifier': identifier,
            'owner': owner,
            'DomainName': owner,
            'httpStatus': self.resp.status_code if self.resp is not None else 0,
            'requestTime': self.head_execution_time,
            'indexedAt': datetime.datetime.utcnow(),
            'crawler': 'v3',
        }
        result.update(self._clusterize_domain_name())

        if self.s3_filename:
            result['contentHash'] = self.s3_filename

        if self.resp:
            result.update({
                'DateCreated': self._get_date_created(),
                'ContentSize': len(self.body),
                # 'MIMEType': self._get_mimetype(),
            })
            result.update(self._get_mimetype())

        if self.resp and self.resp.is_redirect:
            result.update({
                'redirectTo': self.resp.next.url,
            })

        if self.is_html:
            descr = self._get_description(soup)
            if isinstance(descr, str):
                descr = descr.strip()
            result.update({
                'keywords': self.get_keywords(soup) if soup else None
            })
        if self.internal_links:
            result.update({
                'links': self.internal_links,
                'linksCount': len(self.internal_links),
            })
        if self.external_links:
            result.update({
                'externalLinks': self._prefetch_external_links(self.external_links),
                'externalLinksCount': len(self.external_links),
            })
        if getattr(self, 'externalDomains', []):
            result.update({
                'externalDomains': self.external_domains,
                'externalDomainsCount': len(self.external_domains),
            })

        if filename:
            result['filename'] = filename
        if page_title:
            result['Title'] = page_title
        if self.error:
            result['SpiderErrorMessage'] = self.error
        del soup
        return result

    def _prefetch_external_links(self, ext_links):
        """
        For each external link do HEAD request (if it's possible) and return
        the information about the results
        """
        # unhappy gov guys behaviour: just the lit
        return {url: {} for url in ext_links}

        # def fetch_url(url):
        #     time.sleep(random.randint(10, 20))
        #     if isinstance(url, list):
        #         url = url[0]
        #     try:
        #         resp = requests.head(url, allow_redirects=True)
        #         # print("---URL {} code {}".format(url, resp.status_code))
        #         return url, resp, None
        #     except Exception as e:
        #         return url, None, e
        #     # h = httplib2.Http(disable_ssl_certificate_validation=True)
        #     # try:
        #     #     resp, content = h.request(url, "HEAD")
        #     #     return url, resp, None
        #     # except Exception as e:
        #     #     return url, None, e
        #     # finally:
        #     #     del h

        # result = {}
        # start = timer()
        # # results = ThreadPool(20).imap_unordered(fetch_url, ext_links)
        # results = []
        # with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        #     # Start the load operations and mark each future with its URL
        #     head_resps = {
        #         executor.submit(fetch_url, ext_links): url
        #         for url in ext_links
        #     }
        #     for future in concurrent.futures.as_completed(head_resps):
        #         url = head_resps[future]
        #         try:
        #             data = future.result()
        #         except Exception as exc:
        #             print('subscript %r generated an exception: %s' % (url, exc))
        #         else:
        #             # this_worker_crawled_count += 1
        #             # print("URL {} results {}".format(url, data))
        #             results.append(data)
        #             # new_links += data
        #             # print('%r page is %d bytes' % (url, len(data)))
        # for url, resp, exc in results:
        #     http_status = resp.status_code if resp else 0
        #     if exc is None:
        #         result[url] = {
        #             'HttpStatus': http_status,
        #             'Time': round(timer() - start, 6),
        #         }
        #     else:
        #         result[url] = {
        #             'HttpStatus': 0,
        #             'Time': round(timer() - start, 6),
        #             'Error': str(exc)
        #         }
        # return result

    def _guess_filename(self, identifier):
        if '//' in identifier:
            stripped_id = identifier[identifier.index('//')+2:]
        else:
            stripped_id = identifier
        if stripped_id.startswith('www.'):
            stripped_id = stripped_id[len('www.'):]

        if '/' not in stripped_id:
            return None

        filename = None
        try:
            if not stripped_id.endswith('/'):
                # may be it's file?
                last_part = stripped_id.split('/')[-1]
                filename_parts = last_part.split('.')
                if len(filename_parts) > 1:
                    ext = filename_parts[-1]
                    if len(ext) >= 2 and len(ext) <= 8:
                        # looks like a filename!
                        filename = last_part
        except Exception as e:
            logger.exception(e)
        return filename

    def _get_description(self, soup):
        if not soup:
            return 'Binary/skipped file'
        # strict way
        for title_type_name in "og:title", "title":
            meta_title = soup.find("meta",  property=title_type_name)
            if meta_title and meta_title["content"]:
                return meta_title["content"]

        # guess way
        all_paragraphs = [s.extract().text for s in soup('p')]
        ret = ''
        for t in all_paragraphs:
            p_len = len(t)
            if p_len > 150 and 'script' not in t.lower():
                return t
            if p_len > len(ret):
                ret = t
        if not ret:
            ret = soup.get_text(strip=True)
        return ret[:300].strip()

    def _clusterize_domain_name(self):
        result = {
            'jurisdiction': "Commonwealth",
        }
        thirdlvl = ['qld', 'nsw', 'vic', 'nt', 'sa', 'wa', 'tas', 'act']
        domain_parts = self.domain_name.split('.')
        if len(domain_parts) >= 3 and domain_parts[-3] in thirdlvl:
            result['jurisdiction'] = domain_parts[-3].upper()
        elif self.domain_name.endswith('.gov.nf'):
            result['jurisdiction'] = 'Norfolk Island'
        elif self.domain_name.endswith('gov.cx'):
            result['jurisdiction'] = 'Christmas Island'
        elif self.domain_name.endswith('.shire.cc'):
            result['jurisdiction'] = 'Cocos Keeling Islands'
        return result

    def _get_mimetype(self):
        r = {
            # 'MIMEType': None,
        }
        header_value = self.resp.headers.get('Content-Type')
        if header_value:
            if ';' in header_value:  # text/html; charset=utf-8
                mimeparts = header_value.split(';')
                if len(mimeparts) > 0:
                    r['MIMEType'] = mimeparts[0].strip().lower()
                if len(mimeparts) > 1:
                    r['encoding'] = mimeparts[1].strip().lower()
        try:
            if 'MIMEType' in r:
                if '/' in r['MIMEType']:
                    mimetype_parts = r['MIMEType'].split('/')
                    if len(mimetype_parts) > 0:
                        r['MIMEGroup'] = mimetype_parts[0]
                    if len(mimetype_parts) > 1:
                        r['MIMEFormat'] = mimetype_parts[1]
        except Exception as e:
            logger.exception(e)
        return r

    def _get_date_created(self):
        if not self.resp:
            return None
        lm = self.resp.headers.get('last-modified')
        if lm:
            lm = dateutil.parser.parse(lm)
            if lm:
                lm = lm.isoformat()
        return lm

    def get_keywords(self, soup):
        if not soup:
            return None
        kws = set()
        for tag in ['h1', 'h2', 'h3', 'h4']:
            for header in soup.find_all(tag):
                words = [w.strip().strip(',').strip('.') for w in header.text.split() if len(w) > 6]
                for w in words:
                    kws.add(w)
        return [kw.lower() for kw in list(kws) if kw.strip()]

    def _get_language(self):
        return 'en-us'
