import os
import logging
import logging.config

WORKER_NAME = 'crawler'

LOGGING = {
    'version': 1,
    'formatters': {
        'simple': {'format': '%(levelname)s %(message)s'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    },
    WORKER_NAME: {
        'level': 'INFO',
        'handlers': ['console']
    },
}

RAVEN_DSN = os.environ.get('CRAWLER_RAVEN_DSN')
if RAVEN_DSN is not None:
    LOGGING['handlers']['sentry'] = {
        'level': 'WARNING',
        'class': 'raven.handlers.logging.SentryHandler',
        'dsn': RAVEN_DSN,
        'tags': {
            'service': 'crawler',
        },
    }
    LOGGING['root']['handlers'] += ['sentry']
    LOGGING[WORKER_NAME]['handlers'] += ['sentry']

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(WORKER_NAME)
