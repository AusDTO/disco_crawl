#!/usr/bin/env python3
"""
https://lucene.apache.org/core/2_9_4/queryparsersyntax.html
http://elasticsearch-py.readthedocs.io/en/5.5.1/api.html#elasticsearch
"""
import datetime
import time
import random

import boto3
import dateutil.parser
import pytz
import redis

from steward_conf import settings

print("Starting the steward...")
sqs_resource = boto3.resource('sqs', region_name=settings.AWS_REGION)

SEND_PER_ITERATION = 50

recently_sent_domains = set()


def should_be_crawled(domain_name):
    blacklist = [
        ".qld.gov.au", ".nsw.gov.au", ".vic.gov.au", ".nt.gov.au",
        ".sa.gov.au", ".wa.gov.au", ".tas.gov.au", ".act.gov.au",
        '.data.gov.au'
    ]
    if not domain_name.endswith('gov.au'):
        return False
    for bl in blacklist:
        if domain_name.endswith(bl):
            return False
    return True


def crawl_domain(rd):
    print("[{}] Going to crawl {}".format(datetime.datetime.utcnow(), rd))
    requests_queue = sqs_resource.get_queue_by_name(
        QueueName=settings.QUEUE_REQUESTS.split(':')[-1],
        QueueOwnerAWSAccountId=settings.QUEUE_REQUESTS.split(':')[-2]
    )
    recently_sent_domains.add(rd)
    requests_queue.send_message(
        MessageBody=rd
    )
    return


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def is_redis_crawl_locked(domain_name):
    db_locked = redis.StrictRedis(
        host=settings.REDIS_LOCK_ENDPOINT,
        port=6379,
        db=settings.REDIS_LOCK_DB,
        password=settings.REDIS_LOCK_PASSWORD,
    )

    def _check_domain(domain_name):
        recent_crawled_at = db_locked.get("crawled_started_{}".format(domain_name))
        if not recent_crawled_at:
            # no crawl record, good
            return False
        # it's been crawled some time ago, check how long
        parsed_date = dateutil.parser.parse(recent_crawled_at)
        duetime = utcnow() - datetime.timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES)
        if parsed_date:
            if parsed_date > duetime:
                # print("[{}] Won't crawl the domain, locked till {}".format(domain_name, parsed_date))
                return True
        else:
            print("[{}] Unparseable datetime".format(domain_name, recent_crawled_at))
        return False

    # check both www and no-www version, return "locked" if at least one is locked
    if domain_name.startswith('www.'):
        nowww = domain_name[len('www.'):]
        www = domain_name
    else:
        nowww = domain_name
        www = 'www.' + domain_name

    # at least one variant locked - ignore it
    return _check_domain(nowww) or _check_domain(www)


def get_random_noncrawled_domains():
    domains = []

    db_seen = redis.StrictRedis(
        host=settings.REDIS_SEEN_ENDPOINT,
        port=6379,
        db=settings.REDIS_SEEN_DB,
        password=settings.REDIS_SEEN_PASSWORD,
    )
    db_finished = redis.StrictRedis(
        host=settings.REDIS_FINISHED_ENDPOINT,
        port=6379,
        db=settings.REDIS_FINISHED_DB,
        password=settings.REDIS_FINISHED_PASSWORD,
    )

    # potentialy slow procedure, but still okay while we have just like 10 or 20k records
    all_seen_domains = [
        x.decode('utf-8').lower() for x in db_seen.keys('*')
    ]
    random.shuffle(all_seen_domains)

    stats_locked = 0
    stats_recently_seen = 0
    stats_finished = 0

    for domain_name in all_seen_domains:
        domain_name = domain_name.strip()
        # if domain is not crawled yet
        if not should_be_crawled(domain_name):
            # not interesting domain
            continue

        if domain_name in recently_sent_domains:
            stats_recently_seen += 1
            continue

        if db_finished.get(domain_name):
            stats_finished += 1
            continue

        if is_redis_crawl_locked(domain_name):
            stats_locked += 1
            continue

        if len(domains) > SEND_PER_ITERATION * 10:
            break

        domains.append(domain_name)

    print(
        (
            "This iteration: {} domain to be crawled, {} already sent recently,"
            " {} finished, {} redis-locked"
        ).format(
            len(domains),
            stats_recently_seen,
            stats_finished,
            stats_locked
        )
    )

    return domains


def main_cycle():
    sent_some_domains = False
    requests_queue = sqs_resource.get_queue_by_name(
        QueueName=settings.QUEUE_REQUESTS.split(':')[-1],
        QueueOwnerAWSAccountId=settings.QUEUE_REQUESTS.split(':')[-2]
    )
    try:
        pending_messages = int(requests_queue.attributes.get('ApproximateNumberOfMessages'))
    except (ValueError, TypeError) as e:
        print(e)
    else:
        if pending_messages < 10:
            # queue is empty, get some more requests there
            random_domains = get_random_noncrawled_domains()
            domains_to_send = SEND_PER_ITERATION
            sent_some_domains = True
            for rd in random_domains:
                if should_be_crawled(rd):
                    if rd in recently_sent_domains:
                        print("Domain {} has been already sent recently, ignoring it this time".format(rd))
                    else:
                        crawl_domain(rd)
                        domains_to_send -= 1
                        if domains_to_send == 0:
                            break
    return sent_some_domains


# we restart the script each 10 sends, just to make sure it's fresh
till_restart = 100
while till_restart > 0:
    if main_cycle():
        till_restart -= 1
        time.sleep(7)
    time.sleep(5)

print("Steward has finished.")
