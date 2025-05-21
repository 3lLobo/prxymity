import json
from typing import Any, Dict, List, Union


class AlertFormatter:
    """
    A class to format a single alert dictionary into
    a flattened string representation.
    """

    def __init__(self, alert: Dict[str, Any]) -> None:
        """
        Initialize the formatter with an alert dictionary.

        :param alert: A dictionary representing a single alert.
        """
        self.alert = alert
        self.fields: List[str] = [
            "@timestamp",
            "_id",
            "kibana.alert.original_time",
            "kibana.alert.risk_score",
            "kibana.alert.rule.description",
            "kibana.alert.rule.name",
            "kibana.alert.rule.threat.framework",
            "kibana.alert.rule.threat.tactic.id",
            "kibana.alert.rule.threat.tactic.name",
            "kibana.alert.rule.threat.tactic.reference",
            "kibana.alert.rule.threat.technique.id",
            "kibana.alert.rule.threat.technique.name",
            "kibana.alert.rule.threat.technique.reference",
            "kibana.alert.severity",
            "kibana.alert.workflow_status",
            "process.executable",
        ]

    def get_nested(self, d: Dict[str, Any], key_path: str) -> Union[str, int]:
        """
        Safely retrieve a nested value from a dictionary using
        a dotted key path.

        :param d: The dictionary to retrieve the value from.
        :param key_path: A dot-separated string indicating
        the path to the value.
        :return: The value if found and of type str or int,
        otherwise an empty string.
        """
        keys = key_path.split(".")
        for key in keys:
            if isinstance(d, dict):
                d = d.get(key, {})
            else:
                return ""
        return d if isinstance(d, (str, int)) else ""

    def format(self) -> str:
        """
        Format the alert data into a string with CSV-style field-value lines.

        :return: A formatted string representing the alert.
        """
        output = []
        for field in self.fields:
            value = self.get_nested(self.alert, field)
            output.append(f"{field},{value}")
        return "\n".join(output)


class AlertProcessor:
    """
    A class to process a JSON file of alerts and format each alert.
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize the processor with the path to the alerts JSON file.

        :param file_path: Path to the alerts JSON file.
        """
        self.file_path = file_path
        self.data: Dict[str, Any] = self.load_data()

    def load_data(self) -> Dict[str, Any]:
        """
        Load and parse the JSON data from the file.

        :return: A dictionary representing the parsed JSON content.
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def process_alerts(self) -> None:
        """
        Process and format each alert in the JSON data.
        """
        hits = self.data.get("hits", [])
        for hit in hits:
            alert = hit.get("_source", {})
            alert["_id"] = hit.get("_id", "")
            formatter = AlertFormatter(alert)
            print(formatter.format())
            print()  # Spacing between alerts


if __name__ == "__main__":
    processor = AlertProcessor("data/alerts.json")
    processor.process_alerts()
