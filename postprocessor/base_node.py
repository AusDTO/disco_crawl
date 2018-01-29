"""
extend this base_node to:

 * read from a stream
 * process records and
 * (optionally) write to another stream

import main() and run it, passing in your own process_record function

main() will spawn a worker (OS process) for every shard in the stream,
to process the shards in parallel.
"""

import boto3
import json
from datetime import datetime
import time
import multiprocessing

import settings

aws_session = boto3.Session(
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,)
kinesis_client = aws_session.client('kinesis')
s3_client = aws_session.client('s3')
s3_resource = aws_session.resource('s3')


def file_exists_in_bucket(bucket, s3key):
    try:
        head = s3_client.head_object(Bucket=bucket, Key=s3key)
        return True
    except:
        return False


def process_record(num, counter, record, output_stream):
    ''' provide your own process_record function to main() '''
    data = json.loads(record['Data'])

    # do something fantastic with the data here
    # ...

    if output_stream:
        put_json_into_stream(output_stream, data, data['uuid'])


def put_json_into_stream(stream, json_data, part_key):
    global kenesis_client
    kinesis_client.put_record(
        StreamName=stream,
        Data=json.dumps(json_data),
        PartitionKey = part_key
    )

def worker(num, shard_iterator_response, process_record, output_stream):
    counter=0
    while 'NextShardIterator' in shard_iterator_response:
        for record in shard_iterator_response['Records']:
            #print("worker: {}".format(num))
            process_record(num, counter, record, output_stream)
            counter += 1
        # don't impact-drill the kinesis API when end of stream reached
        time.sleep(0.4)
        
        shard_iterator_response = kinesis_client.get_records(
            ShardIterator=shard_iterator_response['NextShardIterator'],
            Limit=int(settings.KINESIS_FETCH_LIMIT)
        )

def main(process_record, input_stream_name, output_stream=None):
    global kinesis_client
    response = kinesis_client.describe_stream(StreamName=input_stream_name)
    jobs=[]
    counter=0
    for shard in response['StreamDescription']['Shards']:
        shard_id = shard['ShardId']
        shard_iterator = kinesis_client.get_shard_iterator(
            StreamName=input_stream_name,
            ShardId=shard_id,
            ShardIteratorType=settings.SHARD_ITERATOR_TYPE
        )
        shard_iterator_id = shard_iterator['ShardIterator']
        shard_iterator_response = kinesis_client.get_records(
            ShardIterator=shard_iterator_id,
            Limit=2
        )
        proc = multiprocessing.Process(
            target=worker,
            args=(counter, shard_iterator_response, process_record, output_stream)
        )
        jobs.append(proc)
        counter += 1
        proc.start()


if __name__ == '__main__':
    main(process_record, settings.STREAM_QUALIFIED_URLS, None)
