import pandas as pd
from elasticsearch import Elasticsearch, helpers

class EmailBeaconDetector:
    def __init__(self, es_host='localhost', es_port=9200, es_index='email-logs-*', min_occur=10, min_percent=5, window=2, period=24, min_interval=2):
        self.es_host = es_host
        self.es_port = es_port
        self.es_index = es_index
        self.min_occur = min_occur
        self.min_percent = min_percent
        self.window = window
        self.period = period
        self.min_interval = min_interval
        self.es = Elasticsearch(self.es_host, port=self.es_port, timeout=60)
        self.data = self._fetch_data()

    def _fetch_data(self):
        # Calculate time range in milliseconds
        import time
        NOW = int(time.time() * 1000)
        HOURS = 60 * 60 * 1000
        gte = NOW - self.period * HOURS

        query = {
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "email.sender"}},
                        {"exists": {"field": "email.receiver"}},
                        {"range": {"@timestamp": {"gte": gte, "lte": NOW, "format": "epoch_millis"}}}
                    ]
                }
            },
            "_source": ["email.sender", "email.receiver", "@timestamp"]
        }

        resp = helpers.scan(query=query, client=self.es, index=self.es_index, scroll="10m", timeout="5m")
        records = [rec['_source'] for rec in resp]
        if not records:
            raise Exception("No email log data found for the specified period.")
        df = pd.DataFrame(records)
        return df

    def _percent_grouping(self, delta_counts, total):
        max_percent = 0
        best_interval = 0
        keys = sorted(delta_counts.keys())
        for i in range(len(keys) - self.window + 1):
            window_keys = keys[i:i + self.window]
            current = sum([delta_counts[k] for k in window_keys])
            percent = (current / total) * 100
            if percent > max_percent:
                max_percent = percent
                best_interval = window_keys[self.window // 2]
        return best_interval, max_percent

    def detect_beaconing(self):
        df = self.data.copy()
        df['pair_id'] = (df['email.sender'] + df['email.receiver']).apply(hash)
        df['@timestamp'] = pd.to_datetime(df['@timestamp'])
        results = []

        for pair_id, group in df.groupby('pair_id'):
            group = group.sort_values('@timestamp')
            group['delta'] = group['@timestamp'].diff().dt.total_seconds().fillna(0).astype(int)
            group = group[group['delta'] >= self.min_interval]
            if group.empty:
                continue
            delta_counts = group['delta'].value_counts().to_dict()
            total = sum(delta_counts.values())
            if total < self.min_occur:
                continue
            interval, percent = self._percent_grouping(delta_counts, total)
            if percent > self.min_percent:
                sender = group['email.sender'].iloc[0]
                receiver = group['email.receiver'].iloc[0]
                results.append({
                    'sender': sender,
                    'receiver': receiver,
                    'interval_seconds': interval,
                    'beacon_percent': percent,
                    'event_count': total
                })
        return pd.DataFrame(results)

# Example usage:
# detector = EmailBeaconDetector()
# beaconing_results = detector.detect_beaconing()
# print(beaconing_results)
