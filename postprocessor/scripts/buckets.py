import boto3

s3 = boto3.resource('s3', region_name='ap-southeast-2')

WORKING_BUCKET = 'monkeypants-demo-delme-stream-stuff'

all_buckets = s3.buckets.all()
print("Found these buckets:")
for bucket in all_buckets:
    print("  * {}".format(bucket.name))

if WORKING_BUCKET not in all_buckets:
    print('')
    s3.create_bucket(
        ACL="private",
        Bucket=WORKING_BUCKET,
        CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-2'},
    )
