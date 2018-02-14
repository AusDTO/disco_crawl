#!/usr/bin/env python
"""
Output the CSV data (console) which shows some typical domain configuration errors
(when we can connect website.name but can't www.website.name or https://website.name)
Ignores the domain name if all variants are failed (assuming the wrong domain)
Configuration: check local.env.sample file
"""
import os
import time

import redis
import requests
import random

HEADERS = {
    'Accept': 'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;',
    'Accept-Encoding': 'gzip,deflate',
    'Cache-Control': 'max-age=0',
    'User-Agent': "Mozilla/5.0 (X11; Fedora; Linux) https://github.com/AusDTO/disco_crawl",
}

CONF = {
    'REDIS_SEEN_ENDPOINT': os.environ.get('REDIS_SEEN_ENDPOINT'),
    'REDIS_SEEN_DB': int(os.environ.get('REDIS_SEEN_DB')),
    'REDIS_SEEN_PASSWORD': os.environ.get('REDIS_SEEN_PASSWORD', None),
}

assert CONF['REDIS_SEEN_ENDPOINT'] and CONF['REDIS_SEEN_DB']


def process_domain_name(domain_name):
    """
    Makes 4 HEAD requests to the website:
        http://domainname
        http://www.domainname
        https://domainname
        https://www.domainname
    and complains if anything is wrong (bad TLS certificate, can't be resolved, etc)
    In the future extra checks may be added:
        wrong SSL version or TLS less than 1.1
        server software broadcasted in headers
        slow responce
        etc
    We assume that 1 second between the 4 requests won't make any problems for any sane website
    Also the probability of hitting N slow and heavy websites with different domain names on
    the same shared hardware is quite low (given we shuffle the websites list)
    """
    if domain_name.startswith('www.'):
        pure_domain = domain_name[len('www.'):]
        www_domain = domain_name
    else:
        pure_domain = domain_name
        www_domain = 'www.' + domain_name
    urls = [
        ('http', pure_domain),
        ('http', www_domain),
        ('https', pure_domain),
        ('https', www_domain),
    ]
    fails = []
    for scheme, domain in urls:
        time.sleep(1)
        try:
            requests.head(
                "{}://{}".format(scheme, domain),
                allow_redirects=False, timeout=10, headers=HEADERS
            )
        except Exception as e:
            fails.append((scheme, domain, str(e)))
    if len(fails) != 4:
        # we ignore domains which have been failed completely, assuming they are wrong
        for scheme, domain, reason in fails:
            print('"{}","{}","{}"'.format(
                scheme, domain, reason.replace('"', '\\"')
            ))
    return


db_seen = redis.StrictRedis(
    host=CONF['REDIS_SEEN_ENDPOINT'],
    port=6379,
    db=CONF['REDIS_SEEN_DB'],
    password=CONF['REDIS_SEEN_PASSWORD'],
)

# potentialy slow procedure, but still okay while we have just like 10 or 20k records
all_seen_domains = [
    x.decode('utf-8').lower() for x in db_seen.keys('*.gov.au')
]
# For script debug just comment the previous Redis line and make this list static
# all_seen_domains = ['defence.gov.au']
random.shuffle(all_seen_domains)

for domain_name in all_seen_domains:
    process_domain_name(domain_name)
