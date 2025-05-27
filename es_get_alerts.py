from typing import List, Dict, Any
import os
import json
from dotenv import load_dotenv
import elasticsearch
from convert_alerts import AlertProcessor
import requests


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


processor = AlertProcessor("data/alerts.json", "data/keys.txt")
res = processor.process_alerts()


def format_prompt(base_prompt: str, alerts: List[str]) -> str:
    """
    Format the prompt for the model.
    :param base_prompt: The base prompt to be used.
    :param alerts: The list of alerts to be formatted.
    :return: The formatted prompt.
    """
    return "\n\n".join(
        [
            base_prompt,
            *alerts,
            '"""',
        ]
    )


model = os.environ.get("LLM_MODEL", "")
base_prompt_path = "prompts/ifp_prompt.txt"
with open(base_prompt_path, "r", encoding="utf-8") as f:
    base_prompt = f.read()

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": format_prompt(base_prompt, res)},
    ],
    # "options": {
    #     "temperature": 0.2,
    # },
}

payload_path = "data/payload.json"
with open(payload_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=4)


LLM_HOST = os.environ.get("LLM_HOST", "http://localhost:11434")
LLM_TOKEN = os.environ.get("LLM_TOKEN", "")
print(model)
headers = {
    "Authorization": f"Bearer {LLM_TOKEN}",
    "Content-Type": "application/json",
}

res = requests.post(
    f"{LLM_HOST}/v1beta/openai/chat/completions",
    headers=headers,
    json=payload,
    verify=False,
    timeout=100,
)
print(res.status_code)
response = res.json()
print(response)

# print(response.prompt_eval_count)
# print(response.eval_count)
print(response, file=open("data/response.txt", "w", encoding="utf-8"))

# print(json.dumps(response.message, indent=4))
print(
    response["choices"][0]["message"]["content"][8:-4].replace("\n", ""),
    file=open(
        "data/content.json",
        "w",
        encoding="utf-8",
    ),
)
