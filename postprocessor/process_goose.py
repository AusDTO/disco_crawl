import boto3
import json
import settings
import tempfile
from goose3 import Goose

from base_node import (
    main,
    put_json_into_stream,
    s3_client,
    s3_resource,
    file_exists_in_bucket
)


def process_record(worker_num, counter, record, output_stream):
    data = json.loads(record['Data'])
    content_hash = data["contentHash"]

    content_raw_fname =  "{}/content_raw".format(content_hash)
    content_goose_fname = "{}/content_goose".format(content_hash)
    content_goose_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_goose_fname)
    if not content_goose_exists:
        # this will not contain escape characters
        raw_content = s3_resource.Object(
            settings.BUCKET_EXTRA, content_raw_fname
        ).get()["Body"].read()
        # so we don't need to interpret them
        g = Goose()
        g.config.enable_image_fetching = False

        article = g.extract(raw_html=raw_content)
        goose_content = bytes(article.cleaned_text, 'utf-8')
        # this may contains some escape character mangling
        goose_content = bytes(goose_content.decode('unicode_escape'), 'utf-8')
        goose_fp = s3_resource.Object(settings.BUCKET_EXTRA, content_goose_fname)
        goose_fp.put(Body=goose_content)
    else:
        goose_content = s3_resource.Object(
            settings.BUCKET_EXTRA, content_goose_fname
        ).get()["Body"].read().decode('utf-8', 'ignore')

    data['content_goose_fname'] = content_goose_fname
    data['content_goose'] = str(goose_content)
    put_json_into_stream(output_stream, data, content_hash)
    print("{}.{} processed {}".format(worker_num, counter, content_hash))

if __name__ == '__main__':
    main(process_record, settings.STREAM_VERIFIED_BS4, settings.STREAM_VERIFIED_GOOSE)
