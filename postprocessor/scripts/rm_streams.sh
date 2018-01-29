#!/bin/bash

echo "Deleting the Kinesis streams"
aws kinesis delete-stream --stream-name qualified_urls
aws kinesis delete-stream --stream-name verified_raw
aws kinesis delete-stream --stream-name verified_textract
aws kinesis delete-stream --stream-name verified_bs4
aws kinesis delete-stream --stream-name verified_goose
aws kinesis delete-stream --stream-name readability_scored

#aws kinesis delete-stream --stream-name model_input
#aws kinesis delete-stream --stream-name demo_delme

