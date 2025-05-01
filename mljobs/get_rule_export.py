#!/usr/bin/env python3

"""
This script is used to export rule json files from an elasticsearch cluster.
"""
import os
import logging
import json
from dotenv import load_dotenv
import requests
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Load environment variables from .env file
load_dotenv()  # take environment variables

ES_FINGERPRINT = os.environ.get("ES_FINGERPRINT", "")
ES_PASSWORD = os.environ.get("ES_PASSWORD", "")
ES_HOST = os.environ.get("ES_HOST", "")
KIBANA_HOST = os.environ.get("KIBANA_HOST", "")
# init session


class DetectionRules:
    def __init__(self, kibana_host, es_fingerprint, es_password):
        self.kibana_host = kibana_host
        self.es_fingerprint = es_fingerprint
        self.es_password = es_password

        session = requests.Session()
        session.auth = ("elastic", ES_PASSWORD)
        session.verify = False
        session.headers.update({"kbn-xsrf": "true"})
        session.headers.update({"Content-Type": "application/json"})
        session.headers.update({"Accept": "application/json"})

        self.session = session
        self.rules = None
        self.rules = self._get_rules()

    def _get_rules(self):
        """
        Get all rules from the elasticsearch cluster
        """
        url = f"{self.kibana_host}/api/detection_engine/rules/_find?page=1&per_page=10000&sort_field=enabled&sort_order=desc"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting rules: {response.status_code}")
            logger.error(f"Error getting rules: {response.text}")
            return None
        
    def export_rules(self, rule_ids=None):
        """
        Export rules from the elasticsearch cluster
        """
        if self.rules is None:
            logger.error("No rules found")
            return None
        filtered_rules = []
        
        if rule_ids is None:
            rule_ids = [rule["id"] for rule in self.rules["data"]]

        if not isinstance(rule_ids, list):
            logger.error("rule_ids must be a list")
            return None
        
        for rule in self.rules["data"]:
            if rule["id"] in rule_ids:
                filtered_rules.append(rule)
        return filtered_rules

    def filter_for_tags(self, tags):
        """
        Filter rules for tags
        """
        if self.rules is None:
            logger.error("No rules found")
            return None
        filtered_rules = []
        for rule in self.rules["data"]:
            if "tags" in rule and any(tag in rule["tags"] for tag in tags):
                filtered_rules.append(rule)
        return filtered_rules
    
    def get_tags(self):
        """
        Get all tags from the elasticsearch cluster
        """
        if self.rules is None:
            logger.error("No rules found")
            return None
        tags = set()
        for rule in self.rules["data"]:
            if "tags" in rule:
                tags.update(rule["tags"])
        return list(tags)
    
    

dr = DetectionRules(
    kibana_host=KIBANA_HOST,
    es_fingerprint=ES_FINGERPRINT,
    es_password=ES_PASSWORD,
)

print(dr.get_tags())

# Get all rules
rules = dr.export_rules()


with open("data/rules.json", "w") as f:
    json.dump(
        rules,
        f,
        indent=2,
    )
