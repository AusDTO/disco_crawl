import boto3
import json
import settings
import tempfile
from bs4 import BeautifulSoup

from base_node import (
    main,
    put_json_into_stream,
    s3_client,
    s3_resource,
    file_exists_in_bucket
)


def process_record(worker_num, counter, record, output_stream):
    data = json.loads(json.loads(record['Data']))
    #print(json.dumps(data, indent=4))
    content_hash = data["contentHash"]
    content_raw_fname = "{}/content_raw".format(content_hash)
    content_bs4_fname = "{}/content_bs4".format(content_hash)
    content_bs4_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_bs4_fname)
    if not content_bs4_exists:
        # this may contain escape characters
        raw_content = s3_resource.Object(
            settings.BUCKET_EXTRA, content_raw_fname
        ).get()["Body"].read()
        # so, we need to interpret them
        try:
            raw_content = bytes(raw_content.decode("unicode_escape"), 'utf-8')
        except:
            print("{}.{} problem decoding {}".format(
                worker_num, counter, content_hash)) # or not...
            return False

        soup = BeautifulSoup(raw_content, "lxml")
        for script in soup(["script", "style"]):
            script.extract()
        bs4_content = bytes(soup.get_text(), 'utf-8')
        #print(bs4_content.decode('ascii', 'ignore'))

        bs4_fp = s3_resource.Object(settings.BUCKET_EXTRA, content_bs4_fname)
        bs4_fp.put(Body=bs4_content)
    else:
        # this does not contain escape characters
        bs4_content = s3_resource.Object(
            settings.BUCKET_EXTRA, content_bs4_fname
        ).get()["Body"].read()

    # do something with bs4_content now?
    data['content_bs4_fname'] = content_bs4_fname
    put_json_into_stream(output_stream, data, content_hash)
    print("{}.{} processed {}".format(worker_num, counter, content_hash))
    #print(json.dumps(data, indent=4))

if __name__ == '__main__':
    main(process_record, settings.STREAM_VERIFIED_RAW, settings.STREAM_VERIFIED_BS4)
