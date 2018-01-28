import json
import settings
from base_node import main

def process_record(worker_num, counter, record, output_stream):
    data = json.loads(record['Data'])

    # do something fantastic with the data here
    print(data['contentHash'])

if __name__ == '__main__':
    main(process_record, settings.STREAM_MODEL_INPUT, None)
