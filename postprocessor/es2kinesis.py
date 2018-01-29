"""
for now, this script just grabs a limited number of records for dev purposes

it should grab all records that have not been post-processed, such that it 
can be re-run in the future to scoop up any new crawled pages (assuming the
current queue has been processed, then it will be efficient).
"""
import boto3
import json
from datetime import datetime
import calendar
import random
import time
import uuid
from base_node import kinesis_client

import settings

my_stream_name = settings.STREAM_QUALIFIED_URLS

ATTR_NAMES = (
    "ContentSize", "DateCreated", "DomainName", "MIMEFormat",
    "MIMEGroup", "MIMEType", "Title", "contentHash", "crawler",
    "encoding", "externalDomainsCount", "externalLinksCount",
    "httpStatus", "identifier", "indexedAt", "jurisdiction",
    "linksCount", "owner", "uuid", "requestTime")

# The strange double-encoding may be a bug, definitely
# requires special handling...
DOUBLE_ENCODED_ATTRS = ("externalLinks",)

LIST_ATTR_NAMES = (
    "externalDomains",
    "keywords", "links")


if __name__ == "__main__":
    from elasticsearch import Elasticsearch
    from elasticsearch_dsl import Search
    client = Elasticsearch(settings.ES_URL)
    s = Search(
        using=client,
        index="webindex-search-staging"
    ).query(
        "match",
        jurisdiction="Commonwealth"
    ).query(
        "match",
        DomainName="www.environment.gov.au"
    ).query(
        "match",
        keywords="climate"
    ).query(
        "match",
        keywords="science"
    )
    
    '''.query(
        "match",
        domain="www.environment.gov.au"
    ) #biodiversity"
    '''
    count = s.count()
    print("records found: {}".format(count))

    fetched=0
    # will this method work for millions of records, or
    # should I be chunking it up be domain name (for example)?
    for hit in s.scan():
        fetched += 1
        if fetched % 70 == 0:
            print('. [{}]'.format(fetched), flush=True)
        else:
            print('.', end='', flush=True)
        
        # hit is AttrDict, not an actual dictionary (yet)        
        data = {}
        for attr_name in ATTR_NAMES:
            data[attr_name] = getattr(hit, attr_name, None)
        for list_attr_name in LIST_ATTR_NAMES:
            my_list = []
            for item in getattr(hit, list_attr_name, ()):
                my_list.append(item)
            data[list_attr_name] = my_list
        for attr_name in DOUBLE_ENCODED_ATTRS:
            attr_val = getattr(hit, attr_name, None)
            if attr_val:
                data[attr_name] = json.loads(attr_val)
            else:
                # we don't actually care
                # print("no {} attribute on {}".format(attr_name, hit))
                pass

        kinesis_client.put_record(
            StreamName=my_stream_name,
            Data=json.dumps(data),
            PartitionKey=getattr(data, "contentHash",  str(uuid.uuid4())))
    print('')
    print('DONE.')
