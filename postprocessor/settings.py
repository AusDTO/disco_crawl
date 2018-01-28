from envparse import env

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default=None)

BUCKET_CONTENTHASH = env('BUCKET_CONTENTHASH', default='webindex-storage-staging')
BUCKET_EXTRA = env('BUCKET_EXTRA', default='webindex-storage-staging-extra')
STREAM_QUALIFIED_URLS = env('STREAM_QUALIFIED_URLS', default='qualified_urls')
STREAM_VERIFIED_RAW = env('STREAM_VERIFIED_RAW', default='verified_raw')
STREAM_VERIFIED_TEXTRACT = env('STREAM_VERIFIED_TEXTRACT', default='verified_textract')
STREAM_VERIFIED_BS4 = env('STREAM_VERIFIED_BS4', default='verified_bs4')
STREAM_VERIFIED_GOOSE = env('STREAM_VERIFIED_GOOSE', default='verified_goose')
AWS_REGION = env('AWS_REGION', default='ap-southeast-2')
ES_URL = env('ES_URL', default=None)
KINESIS_FETCH_LIMIT = env('KINESIS_FETCH_LIMIT', 100)

# for dev/debugging only
SHARD_ITERATOR_TYPE = env('SHARD_ITERATOR_TYPE', 'LATEST')
#SHARD_ITERATOR_TYPE = 'TRIM_HORIZON'
