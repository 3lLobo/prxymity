# !/usr/bin/env python3

import os
import json
import logging
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Load environment variables from .env file
load_dotenv()  # take environment variables

CERT_FINGERPRINT = os.environ.get("CERT_FINGERPRINT", "")
ELASTIC_PASSWORD = os.environ.get("ELASTIC_PASSWORD", "")
ES_HOST = os.environ.get("ES_HOST", "")

client = Elasticsearch(
    [ES_HOST],
    ssl_assert_fingerprint=CERT_FINGERPRINT,
    basic_auth=("elastic", ELASTIC_PASSWORD),
)

print(json.dumps(client.info().body, indent=2))

# Get all opened ML jobs

ml_jobs = client.ml.get_job_stats().body

datafeeds = list()

for job in ml_jobs["jobs"]:
    if job.get("job_id").startswith("ded_") and job.get("state") == "closed":
        client.ml.open_job(job_id=job.get("job_id"))
        print(f"Opening job: {job.get('job_id')}")
        print(json.dumps(job, indent=2))
        df_time = dict()
        df_time["df_name"] = f"datafeed-{job.get('job_id')}"
        df_time["latest_record"] = job.get("data_counts", {}).get(
            "latest_record_timestamp"
        )
        datafeeds.append(df_time)
    # if job.get("state") == "opened":
    #     print(job.get("job_id"))
    #     print(job.get("state"))
    #     # print(json.dumps(job, indent=2))
    #     print("=========================================")
    #     datafeeds.append(f"datafeed-{job.get('job_id')}")


# convert timestamp to this format: 2025-04-22 15:15:36


# start datafeed
for datafeed in datafeeds:
    print(f"Starting datafeed: {datafeed}")
    res = client.ml.start_datafeed(
        datafeed_id=datafeed["df_name"],
        start=str(datafeed["latest_record"]),
        end="now",
    )
    print(json.dumps(res.body, indent=2))


# client.ml.open_job(job_id="ded_high_sent_bytes_destination_ip")

# # import time

# # time.sleep(3)

# ml_status = client.ml.get_job_stats(
#     job_id="ded_high_sent_bytes_destination_geo_country_iso_code"
# )


# # print json object
# ml_status = ml_status.body


# print(json.dumps(ml_status, indent=2))


# # client.ml.forecast()
