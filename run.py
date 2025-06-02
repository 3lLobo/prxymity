import os
import json
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#  add directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/code")
from EnvConfig import EnvironmentConfig
from LlmClient import LLMClient
from FileManager import FileManager
from AlertProcessor import AlertProcessor
from EsClient import ElasticsearchClient, AlertQuery

config = EnvironmentConfig()

es = ElasticsearchClient(config)
llm_client = LLMClient(config.llm_host, config.llm_token)

case_id = "6ef42408-5c83-4c4e-bcb3-cc5aaf2bd479"
alert_ids = es.get_alert_ids_for_case(case_id)
query = AlertQuery.alerts_by_id(alert_ids)

# size = 11
# severity = "medium"  # "low", "medium", "critical"
# query = AlertQuery.new_alerts(size, severity)
index = ".internal.alerts-sec*"

alerts = es.fetch_alerts(query, index)
FileManager.write_json("data/alerts.json", alerts)

processor = AlertProcessor("data/alerts.json", "data/keys.txt")
processed_alerts = processor.process_alerts()

base_prompt = FileManager.read_text("prompts/ifp_prompt.txt")
formatted_prompt = AlertProcessor.format_prompt(base_prompt, processed_alerts)

payload = {
    "model": config.llm_model,
    "messages": [{"role": "user", "content": formatted_prompt}],
}
FileManager.write_json("data/payload.json", payload)

response = llm_client.send_prompt(payload)
FileManager.write_text("data/response.txt", json.dumps(response, indent=4))

content = response["choices"][0]["message"]["content"]
FileManager.write_text("data/content.json", content)
