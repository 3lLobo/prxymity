import os
from dotenv import load_dotenv


class EnvironmentConfig:
    def __init__(self):
        load_dotenv()
        self.es_host = os.getenv("ES_HOST")
        self.es_fingerprint = os.getenv("ES_FINGERPRINT")
        self.es_user = os.getenv("ES_USER")
        self.es_password = os.getenv("ES_PASSWORD")
        self.es_apikey = os.getenv("ES_APIKEY", "")
        self.kibana_host = os.getenv("KIBANA_HOST", "")
        self.llm_host = os.getenv("LLM_HOST", "http://localhost:11434")
        self.llm_model = os.getenv("LLM_MODEL", "")
        self.llm_token = os.getenv("LLM_TOKEN", "")
