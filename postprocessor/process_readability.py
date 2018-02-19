import boto3
import json
import settings
import tempfile
from goose3 import Goose

from base_node import (
    main,
    put_json_into_stream,
    s3_client,
    s3_resource,
    file_exists_in_bucket
)

from readability_score.calculators.ari import ARI
from readability_score.calculators.colemanliau import ColemanLiau
from readability_score.calculators.dalechall import DaleChall
from readability_score.calculators.flesch import Flesch
from readability_score.calculators.fleschkincaid import FleschKincaid
from readability_score.calculators.linsearwrite import LinsearWrite
from readability_score.calculators.smog import SMOG

DEBUG=True


def process_record(worker_num, counter, record, output_stream):
    data = json.loads(record['Data'])
    content_hash = data["contentHash"]

    try:
        goose_str = str(data["content_goose"])
    except:
        content_goose_fname = "{}/content_goose".format(content_hash)
        content_goose_exists = file_exists_in_bucket(settings.BUCKET_EXTRA, content_goose_fname)
        if content_goose_exists:
            goose_str = str(
                s3_resource.Object(
                    settings.BUCKET_EXTRA,
                    content_goose_fname
                ).get()["Body"].read()
            )
        else:
            print("{}.{} ERROR no goose_content {}".format(worker_num, counter, content_hash))
            return False

    data["readability_score_ARI"] = ARI(goose_str).min_age
    data["readability_score_ColemanLiau"] = ColemanLiau(goose_str).min_age
    data["readability_score_DaleChall"] = DaleChall(goose_str).min_age
    data["readability_score_Flesch"] = Flesch(goose_str).min_age
    data["readability_score_FleschKincaid"] = FleschKincaid(goose_str).min_age
    data["readability_score_LinsearWrite"] = LinsearWrite(goose_str).min_age
    data["readability_score_SMOG"] = SMOG(goose_str).min_age
    
    put_json_into_stream(output_stream, data, content_hash)
    print("{}.{} processed {}".format(worker_num, counter, content_hash))
    if DEBUG:
        keys = (
            "readability_score_ARI", "readability_score_ColemanLiau",
            "readability_score_DaleChall", "readability_score_Flesch",
            "readability_score_FleschKincaid", "readability_score_LinsearWrite",
            "readability_score_SMOG"
        )
        try:
            content = data["content_goose"].encode('utf8', 'ignore')
            for k in keys:
                print("{}: {}".format(k, data[k]))
            print(content)
            print("------------------------------------------------------------------")
            print("")
        except:
            pass

if __name__ == '__main__':
    main(process_record, settings.STREAM_VERIFIED_GOOSE, settings.STREAM_READABILITY_SCORED)
