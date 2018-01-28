import json
import settings
from base_node import main, put_json_into_stream

def process_record(worker_num, counter, record, output_stream):
    global kinesis_client
    data = json.loads(record['Data'])

    # do something fantastic with the data here
    msg = "worker {} [record {}] url: {}"
    print(msg.format(worker_num, counter, data['identifier']))

    if output_stream:
        put_json_into_stream(output_stream, data, data['uuid'])

if __name__ == '__main__':
    main(process_record, settings.STREAM_QUALIFIED_URLS, None)
