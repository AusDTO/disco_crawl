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

'''
aws_session = boto3.Session(
    profile_name=settings.AWS_PROFILE,
    region_name=settings.AWS_REGION)
'''
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

"""
SHARD_ITERATOR_TYPE AWS Docs:
 * AT_SEQUENCE_NUMBER - Start reading from the position denoted
   by a specific sequence number, provided in the value
   StartingSequenceNumber.
 * AFTER_SEQUENCE_NUMBER - Start reading right after the position
   denoted by a specific sequence number, provided in the value
   StartingSequenceNumber.
 * AT_TIMESTAMP - Start reading from the position denoted by a
   specific time stamp, provided in the value Timestamp.
 * TRIM_HORIZON - Start reading at the last untrimmed record in
   the shard in the system, which is the oldest data record in 
   the shard.
 * LATEST - Start reading just after the most recent record in
   the shard, so that you always read the most recent data in
   the shard.

We might want some database with ShardSequenceNumber checkpointing
and AT_SEQUENCE_NUMBER. Until then, TRIM_HORIZON (with idempotent
processing steps, check S3 etc).
"""
SHARD_ITERATOR_TYPE = settings.SHARD_ITERATOR_TYPE
#'LATEST' # for dev/debugging only
#SHARD_ITERATOR_TYPE = 'TRIM_HORIZON'


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
            ShardIteratorType=SHARD_ITERATOR_TYPE
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
