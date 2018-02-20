import time
import os

import statsd

host = os.environ.get('CRAWLER_STATSD_HOST')
if host:
    scl = statsd.StatsClient(
        host,
        8125,
        prefix=os.environ.get('CRAWLER_STATSD_PREFIX', 'default-crawler3-prefix')
    )
else:
    scl = statsd.StatsClient('localhost', 8125)


def statsd_timer(counter_name):
    def decorator(method):
        def timed(*args, **kw):
            ts = time.time()
            result = None
            try:
                result = method(*args, **kw)
            except Exception:
                raise
            else:
                te = time.time()
                msecs = (te - ts) * 1000
                if host:
                    scl.timing(counter_name, msecs)
                # else:
                #     print("    [TIMING] {}: {}ms".format(counter_name, int(msecs)))
            return result
        return timed
    return decorator
