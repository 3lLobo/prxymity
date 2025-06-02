from typing import List, Dict, Any
from elasticsearch import Elasticsearch
import requests


class ElasticsearchClient:
    def __init__(self, config):
        self.config = config
        if config.es_apikey:
            self.client = Elasticsearch(
                hosts=[config.es_host],
                api_key=config.es_apikey,
                verify_certs=False,
                ca_certs=config.es_fingerprint,
            )
        else:
            self.client = Elasticsearch(
                hosts=[config.es_host],
                http_auth=(config.es_user, config.es_password),
                verify_certs=False,
                ca_certs=config.es_fingerprint,
            )

    def fetch_alerts(
        self, query: Dict[str, Any], index: str = "*"
    ) -> List[Dict[str, Any]]:
        """
        Fetch alerts from Elasticsearch based on the provided query and index.
        :param query: The query to filter alerts.
        :param index: The index to search in. If empty, defaults to "*".
        :return: A list of alerts matching the query.
        """
        response = self.client.search(index=index, body=query, pretty=True)
        return response["hits"]["hits"]

    def get_alert_ids_for_case(self, case_id: str) -> List[str]:
        """
        Fetch alert IDs associated with a given case ID from Kibana.
        :param case_id: The ID of the case to fetch alerts for.
        :return: A list of alert IDs associated with the case.
        """
        url = f"{self.config.kibana_host}/api/cases/{case_id}/alerts"
        headers = {
            "kbn-xsrf": "true",  # Required by Kibana for API calls
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {self.config.es_apikey}",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                verify=False,
                timeout=10,
            )
            response.raise_for_status()
            alerts = response.json()
            return [alert["id"] for alert in alerts]
        except requests.RequestException as e:
            print(f"Error fetching alerts for case {case_id}: {e}")
            return []


class AlertQuery:
    def __init__(self):
        """
        Initialize the AlertQuery class.
        This class is responsible for building queries to fetch alerts from Elasticsearch.
        """
        pass

    @staticmethod
    def new_alerts(size: int = 11, severity: str = "medium") -> Dict[str, Any]:
        """
        Build a query to fetch new alerts based on severity and size.
        :param size: The number of alerts to fetch.
        :param severity: The severity level of the alerts to fetch.
        :return: The query to fetch new alerts.
        """
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
        return query

    @staticmethod
    def alerts_by_id(alert_ids: List[str]) -> Dict[str, Any]:
        """
        Build a query to fetch alerts by their IDs.
        :param alert_ids: A list of alert IDs to fetch.
        :return: The query to fetch alerts by ID.
        """
        for alert_id in alert_ids:
            print(alert_id)
        query = {
            "size": len(alert_ids),
            "query": {
                "terms": {
                    "_id": alert_ids,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
        }
        return query
