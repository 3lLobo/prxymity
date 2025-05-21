import json
from typing import Any, Dict, List, Union


class AlertFormatter:
    """
    A class to format a single alert dictionary into
    a flattened string representation.
    """

    def __init__(
        self,
        alert: Dict[str, Any],
        fields: List[str] = None,
    ) -> None:
        """
        Initialize the formatter with an alert dictionary.

        :param alert: A dictionary representing a single alert.
        :param fields: A list of fields to include in the output.
        """
        self.alert = alert
        self.fields = fields or []

    def get_nested(self, d: Dict[str, Any], key_path: str) -> Union[str, int]:
        """
        Safely retrieve a nested value from a dictionary using
        a dotted key path.

        :param d: The dictionary to search.
        :param key_path: A dot-separated string indicating
        the path to the value.
        :return: The value if found and of type str or int,
        otherwise an empty string.
        """
        keys = key_path.split(".")
        # deep copy the dictionary to avoid modifying the original
        for key in keys:
            if isinstance(d, list):
                d = d[0] if d else {}

            if isinstance(d, dict):
                d = d.get(key, {})
            else:
                return ""
        if isinstance(d, (str, int)):
            return d
        if isinstance(d, float):
            return int(d)
        elif isinstance(d, list):
            return ", ".join(str(item) for item in d)

        return ""

    def format(self) -> str:
        """
        Format the alert data into a string with CSV-style field-value lines.

        :return: A formatted string representing the alert.
        """
        output = []
        field_threat = "kibana.alert.rule.threat"

        for field in self.fields:
            if field in self.alert.keys():
                value = self.alert.get(field, "")

            elif field.startswith(field_threat):
                # Handle nested fields under "kibana.alert.rule.threat"
                nested_field = field[len(field_threat) + 1 :]
                nested_alert = self.alert.copy().get(field_threat, {})
                value = self.get_nested(nested_alert, nested_field)

            else:
                value = self.get_nested(self.alert.copy(), field)

            if value:
                if field.startswith("kibana.alert"):
                    # Remove the prefix "kibana.alert."
                    field = field[len("kibana.alert.") :]

                output.append(f"{field},{value}")
            # else:
            #     output.append(f"Field '{field}' not found in alert data.")

        return "\n".join(output)


class AlertProcessor:
    """
    A class to process a JSON file of alerts and format each alert.
    """

    def __init__(self, file_path: str, key_path: str) -> None:
        """
        Initialize the processor with the path to the alerts JSON file.

        :param file_path: Path to the alerts JSON file.
        """
        self.file_path = file_path
        self.key_path = key_path
        self.data: Dict[str, Any] = self._load_data()
        self.keys: List[str] = self._load_keys()

    def _load_keys(self) -> List[str]:
        """
        Load the keys from a list file.

        :return: A list of keys to be used for formatting.
        """
        with open(self.key_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f]

    def _load_data(self) -> Dict[str, Any]:
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
        hits = self.data
        for hit in hits:
            alert = hit.get("_source", {})
            alert["_id"] = hit.get("_id", "")
            formatter = AlertFormatter(alert, fields=self.keys)
            print(formatter.format())
            print()  # Spacing between alerts


if __name__ == "__main__":
    processor = AlertProcessor("data/alerts.json", "data/keys.txt")
    processor.process_alerts()
