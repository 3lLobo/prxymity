import json

# Load the alerts.json file
with open("data/alerts.json", "r") as f:
    data = json.load(f)


# Flattening and formatting function
def format_alert(alert):
    fields = [
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

    def get_nested(d, keys):
        for key in keys.split("."):
            d = d.get(key, {})
        return d if isinstance(d, str) or isinstance(d, int) else ""

    output = []
    for field in fields:
        value = get_nested(alert, field)
        output.append(f"{field},{value}")
    return "\n".join(output)


# Extract and print alerts
hits = data.get("hits", [])
for hit in hits:
    alert = hit.get("_source", {})
    alert["_id"] = hit.get("_id", "")
    print(format_alert(alert))
    print()  # Add spacing between alerts
