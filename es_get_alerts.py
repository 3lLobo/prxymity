import elasticsearch
from dotenv import load_dotenv
import os
import json

load_dotenv()
# Load environment variables from .env file
ES_HOST = os.getenv("ES_HOST")
ES_FINGERPRINT = os.getenv("ES_FINGERPRINT")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")

es = elasticsearch.Elasticsearch(
    hosts=[ES_HOST],
    http_auth=(ES_USER, ES_PASSWORD),
    verify_certs=False,
    # use_ssl=True,
    ca_certs=ES_FINGERPRINT,
)
size = 11
severity = "medium"  # "low", "medium", "critical"
#  filter for severity critical
query = {
    "size": size,
    "sort": [{"@timestamp": {"order": "desc"}}],
    "query": {
        "bool": {
            "must": [
                {"term": {"kibana.alert.severity": severity}},
                {"term": {"kibana.alert.workflow_status": "open"}},
            ]
        }
    },
}

index = ".internal.alerts-sec*"
res = es.search(index=index, body=query, pretty=True)
alerts = res["hits"]["hits"]
# save alerts
with open("data/alerts.json", "w", encoding="utf-8") as f:
    json.dump(alerts, f, indent=4)

from convert_alerts import AlertProcessor

processor = AlertProcessor("data/alerts.json", "data/keys.txt")
processor.process_alerts()
