#!/bin/bash

echo "Ensuring the Kinesis streams exist"
aws kinesis create-stream \
    --stream-name qualified_urls \
    --shard-count 1 \
    --profile difchain-digitalrecords-integration \
    --region ap-southeast-2

aws kinesis create-stream \
    --stream-name verified_raw \
    --shard-count 1 \
    --profile difchain-digitalrecords-integration \
    --region ap-southeast-2


aws kinesis create-stream \
    --stream-name verified_textract \
    --shard-count 1 \
    --profile difchain-digitalrecords-integration \
    --region ap-southeast-2

# 6 of these because the next step (goose) is slow
aws kinesis create-stream \
    --stream-name verified_bs4 \
    --shard-count 6 \
    --profile difchain-digitalrecords-integration \
    --region ap-southeast-2


aws kinesis create-stream \
    --stream-name verified_goose \
    --shard-count 1 \
    --profile difchain-digitalrecords-integration \
    --region ap-southeast-2

#aws kinesis create-stream --stream-name demo_delme --shard-count 1

