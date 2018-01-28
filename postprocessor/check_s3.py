import boto3
import json
import settings
import tempfile
import textract
from bs4 import BeautifulSoup
from goose3 import Goose

from base_node import (
    main,
    put_json_into_stream
    s3_client,
    s3_resource,
    file_exists_in_bucket
)

def file_exists_in_bucket(bucket, s3key):
    try:
        head = s3_client.head_object(Bucket=bucket, Key=s3key)
        return True
    except:
        return False


def process_record(worker_num, counter, record, output_stream):
    ''' overwrite/substitute this in real workers. '''
    data = json.loads(record['Data'])

    # do something fantastic with the data here
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
        raw_content = s3_resource.Object(
            settings.BUCKET_CONTENTHASH, content_hash
        ).get()["Body"].read()

        content_raw_fname =  "{}/content_raw".format(content_hash)
        content_raw_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_raw_fname)
        if not content_raw_exists:
            # make a copy of the raw content in our working s3
            # this is a debug thing, we can stop doing it later
            raw_fp = s3_resource.Object(settings.BUCKET_CONTENTHASH, content_raw_fname)
            raw_fp.put(Body=str(raw_content))

        content_textract_fname = "{}/content_textract".format(content_hash)
        content_textract_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_textract_fname)
        if not content_textract_exists:
            # this contains javascript/css rubbish - textract bug?
            content_file = tempfile.NamedTemporaryFile(suffix=".html")
            raw_local_fp=open(content_file.name, 'w')
            raw_local_fp.write(str(raw_content))
            raw_local_fp.close()  # flush write
            textracted_content = textract.process(content_file.name)
            textract_fp = s3_resource.Object(settings.BUCKET_CONTENTHASH, content_textract_fname)
            textract_fp.put(Body=str(textracted_content))
            content_file.close() # cleans-up
        
        content_bs4_fname = "{}/content_bs4".format(content_hash)
        content_bs4_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_bs4_fname)
        if not content_bs4_exists:
            soup = BeautifulSoup(raw_content, "lxml")
            for script in soup(["script", "style"]):
                script.extract()
            bs4_content = soup.get_text()
            lines = (line.strip() for line in bs4_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            bs4_content = '\n'.join(chunk for chunk in chunks if chunk)
            bs4_fp = s3_resource.Object(settings.BUCKET_CONTENTHASH, content_bs4_fname)
            bs4_fp.put(Body=str(bs4_content))

        content_goose_fname = "{}/content_goose".format(content_hash)
        content_goose_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_goose_fname)
        if not content_goose_exists:
            g = Goose()
            article = g.extract(raw_html=raw_content)
            goose_content = article.cleaned_text
            goose_fp = s3_resource.Object(settings.BUCKET_CONTENTHASH, content_goose_fname)
            goose_fp.put(Body=str(goose_content))
        else:
            goose_content = s3_resource.Object(
                settings.BUCKET_CONTENTHASH, content_goose_fname
            ).get()["Body"].read()
        data['content_goose'] = goose_content
        
        put_json_into_stream(output_stream, data, content_hash)
        return True
    else:
        print("ERROR contentHash {} specified but does not exist".format(content_hash))
        return False


if __name__ == '__main__':
    main(process_record, settings.STREAM_QUALIFIED_URLS, settings.STREAM_MODEL_INPUT)
