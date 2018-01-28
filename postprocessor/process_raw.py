import boto3
import json
import settings
import tempfile
#import textract
#from bs4 import BeautifulSoup
#from goose3 import Goose

from base_node import (
    main,
    put_json_into_stream,
    s3_client,
    s3_resource,
    file_exists_in_bucket
)


def process_record(worker_num, counter, record, output_stream):
    data = json.loads(record['Data'])

    try:
        url = data["identifier"]
    except:
        print("ERROR MYSTERY_IDENTIFIER record has no identifier")
        return False
    
    try:
        content_hash = data["contentHash"]
    except:
        print("ERROR URL {} has no contentHash specified".format(url))
        return False

    src_exists = file_exists_in_bucket(settings.BUCKET_CONTENTHASH, content_hash)
    if src_exists:
        # this may contain escape sequences
        raw_content = str(s3_resource.Object(
            settings.BUCKET_CONTENTHASH, content_hash
        ).get()["Body"].read())
        # so, we need to interpret them
        raw_content = bytes(raw_content, "utf-8").decode("unicode_escape")
        #print(bytes(raw_content, 'utf-8').decode('ascii','ignore'))

        content_raw_fname =  "{}/content_raw".format(content_hash)
        content_raw_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_raw_fname)
        if not content_raw_exists:
            # make a copy of the raw content in our working s3
            # this is a debug thing, we can stop doing it later
            raw_fp = s3_resource.Object(settings.BUCKET_EXTRA, content_raw_fname)
            raw_fp.put(Body=raw_content)
        else:
            # this does not contain escape sequences
            raw_content = s3_resource.Object(
                settings.BUCKET_EXTRA, content_raw_fname
            ).get()["Body"].read()

        data['content_raw_fname'] = content_raw_fname
        put_json_into_stream(output_stream, json.dumps(data), content_hash)
        print("{}.{} processed {}".format(worker_num, counter, content_hash))
    

if __name__ == '__main__':
    main(process_record, settings.STREAM_QUALIFIED_URLS, settings.STREAM_VERIFIED_RAW)
