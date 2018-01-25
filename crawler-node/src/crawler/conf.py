import os


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


settings = AttrDict({
    'STORAGE_BUCKET': os.environ.get('STORAGE_BUCKET', 'dev-storage-bucket'),
    'STORAGE_BUCKET_PREFIX': os.environ.get('STORAGE_BUCKET_PREFIX', ''),
    'QUEUE_REQUESTS': os.environ.get('QUEUE_REQUESTS'),
    'AWS_REGION': os.environ.get('AWS_REGION', 'ap-southeast-2'),

    'MAX_RESULTS_PER_DOMAIN': int(os.environ.get('MAX_RESULTS_PER_DOMAIN') or 500),
    'DOWNLOAD_DELAY': int(os.environ.get('DOWNLOAD_DELAY', 5)),

    'ANALYTICS_ES_ENDPOINT': os.environ.get('ANALYTICS_ES_ENDPOINT'),
    'ANALYTICS_ES_INDEX_NAME': os.environ.get('ANALYTICS_ES_INDEX_NAME'),

    'WORKERS': int(os.environ.get('WORKERS_COUNT', 1)),

    'REDIS_LOCK_ENDPOINT': os.environ.get('REDIS_LOCK_ENDPOINT'),
    'REDIS_LOCK_DB': int(os.environ.get('REDIS_LOCK_DB')),
    'REDIS_LOCK_PASSWORD': os.environ.get('REDIS_LOCK_PASSWORD', None),
    'LOCK_TIMEOUT_MINUTES': int(os.environ.get('LOCK_TIMEOUT_MINUTES', 30)),

    'REDIS_FINISHED_ENDPOINT': os.environ.get('REDIS_FINISHED_ENDPOINT'),
    'REDIS_FINISHED_DB': int(os.environ.get('REDIS_FINISHED_DB')),
    'REDIS_FINISHED_PASSWORD': os.environ.get('REDIS_FINISHED_PASSWORD', None),

    'REDIS_SEEN_ENDPOINT': os.environ.get('REDIS_SEEN_ENDPOINT'),
    'REDIS_SEEN_DB': int(os.environ.get('REDIS_SEEN_DB')),
    'REDIS_SEEN_PASSWORD': os.environ.get('REDIS_SEEN_PASSWORD', None),
})

settings['ANALYTICS_ES_CRAWLED_INDEX_NAME'] = settings.ANALYTICS_ES_INDEX_NAME + "-crawled"

assert settings['QUEUE_REQUESTS'], "Please fill the QUEUE_REQUESTS env variable"
