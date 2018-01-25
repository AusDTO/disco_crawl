import os


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


settings = AttrDict({
    'QUEUE_REQUESTS': os.environ.get('QUEUE_REQUESTS'),
    'AWS_REGION': os.environ.get('AWS_REGION', 'ap-southeast-2'),
    'ANALYTICS_ES_ENDPOINT': os.environ.get('ANALYTICS_ES_ENDPOINT'),
    'ANALYTICS_ES_INDEX_NAME': os.environ.get('ANALYTICS_ES_INDEX_NAME'),
    'ANALYTICS_ES_CRAWLED_INDEX_NAME': os.environ.get('ANALYTICS_ES_INDEX_NAME') + '-crawled',

    'REDIS_LOCK_ENDPOINT': os.environ.get('REDIS_LOCK_ENDPOINT'),
    'REDIS_LOCK_DB': int(os.environ.get('REDIS_LOCK_DB')),
    'REDIS_LOCK_PASSWORD': os.environ.get('REDIS_LOCK_PASSWORD', None),
    'LOCK_TIMEOUT_MINUTES': int(os.environ.get('LOCK_TIMEOUT_MINUTES', 10)),

    'REDIS_FINISHED_ENDPOINT': os.environ.get('REDIS_FINISHED_ENDPOINT'),
    'REDIS_FINISHED_DB': int(os.environ.get('REDIS_FINISHED_DB')),
    'REDIS_FINISHED_PASSWORD': os.environ.get('REDIS_FINISHED_PASSWORD', None),

    'REDIS_SEEN_ENDPOINT': os.environ.get('REDIS_SEEN_ENDPOINT'),
    'REDIS_SEEN_DB': int(os.environ.get('REDIS_SEEN_DB')),
    'REDIS_SEEN_PASSWORD': os.environ.get('REDIS_SEEN_PASSWORD', None),
})
