#!/usr/bin/env python
import redis

from steward_conf import settings


def dump_redis_data():
    """
    Dumps all keys to the console
    """
    db = redis.StrictRedis(
        host=settings.REDIS_FINISHED_ENDPOINT,
        port=6379,
        db=settings.REDIS_FINISHED_DB,
        password=settings.REDIS_FINISHED_PASSWORD,
    )
    for key in db.keys('*'):
        print(key.decode('utf-8'))
    return


if __name__ == '__main__':
    dump_redis_data()
