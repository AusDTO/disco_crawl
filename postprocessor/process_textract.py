import boto3
import json
import settings
import tempfile
import textract
from bs4 import BeautifulSoup
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
    print(data)
    try:
        content_hash = data['contentHash']
    except:
        return False  # DEBUG
    
    content_raw_fname = "{}/content_raw".format(content_hash)
    raw_content = s3_resource.Object(
            settings.BUCKET_EXTRA, content_raw_fname
        ).get()["Body"].read()
    
    content_textract_fname = "{}/content_textract".format(content_hash)
    content_textract_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_textract_fname)
    if not content_textract_exists:
        # this contains javascript/css rubbish - textract bug?
        content_file = tempfile.NamedTemporaryFile(suffix=".html")
        raw_local_fp=open(content_file.name, 'w')
        raw_local_fp.write(str(raw_content))
        raw_local_fp.close()  # flush write
        textract_content = textract.process(content_file.name)
        textract_fp = s3_resource.Object(settings.BUCKET_CONTENTHASH, content_textract_fname)
        textract_fp.put(Body=str(textract_content))
        content_file.close() # clean-up temp file, NamedTemporaryFile magic
        raw_fp = s3_resource.Object(settings.BUCKET_CONTENTHASH, content_raw_fname)
        raw_fp.put(Body=str(raw_content))
    else:
        textract_content = s3_resource.Object(
            settings.BUCKET_CONTENTHASH, content_textract_fname
        ).get()["Body"].read()

    data['content_textract'] = str(textract_content)
    print(data)  # DEBUG
    put_json_into_stream(output_stream, data, content_hash)


if __name__ == '__main__':
    main(process_record, settings.STREAM_VERIFIED_RAW, settings.STREAM_VERIFIED_TEXTRACT)
