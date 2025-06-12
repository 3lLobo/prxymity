import sys
import pandas as pd
from elasticsearch import Elasticsearch, helpers
from multiprocessing import Process, JoinableQueue, Lock, Manager
import time
import datetime
import json
import warnings

warnings.filterwarnings('ignore')


class EmailBeaconDetector:
    def __init__(self,
                 es_host='localhost',
                 es_port=9200,
                 es_index='email-logs-*',
                 period=24,
                 min_occur=10,
                 min_percent=5,
                 window=2,
                 min_interval=2,
                 threads=4,
                 es_timeout=480,
                 verbose=True):
        self.es = Elasticsearch(hosts=[{'host': es_host, 'port': es_port}], timeout=es_timeout)
        self.es_index = es_index
        self.period = period
        self.min_occur = min_occur
        self.min_percent = min_percent
        self.window = window
        self.min_interval = min_interval
        self.threads = threads
        self.verbose = verbose

        self.timestamp_field = '@timestamp'
        self.sender_field = 'email.sender'
        self.receiver_field = 'email.receiver'
        self.size_field = 'email.size'

        self.q_job = JoinableQueue()
        self.l_df = Lock()
        self.l_list = Lock()

        self.fields = [self.sender_field, self.receiver_field, self.size_field,
                       'occurrences', 'percent', 'interval']
        self.high_freq = None
        self.email_data = self.fetch_data()

    def log(self, msg):
        if self.verbose:
            print(f"[INFO] {msg}")

    def fetch_data(self):
        self.log("Fetching email log data from Elasticsearch...")

        now = int(time.time() * 1000)
        start_time = now - self.period * 60 * 60 * 1000  # milliseconds

        query = {
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": self.sender_field}},
                        {"exists": {"field": self.receiver_field}},
                        {"exists": {"field": self.timestamp_field}},
                        {"range": {
                            self.timestamp_field: {
                                "gte": start_time,
                                "lte": now,
                                "format": "epoch_millis"
                            }
                        }}
                    ]
                }
            },
            "_source": [
                self.sender_field,
                self.receiver_field,
                self.timestamp_field,
                self.size_field
            ]
        }

        resp = helpers.scan(client=self.es, index=self.es_index, query=query, scroll="60m", timeout="10m")
        data = pd.json_normalize([doc['_source'] for doc in resp])

        if data.empty:
            raise Exception("No data retrieved. Check index name and field mappings.")

        # Check if receiver field exists and is a list
        if self.receiver_field in data.columns:
            # Explode the receiver list into separate rows
            data = data.explode(self.receiver_field)
            data.reset_index(drop=True, inplace=True)

        data['triad_id'] = (data[self.sender_field] + data[self.receiver_field]).apply(hash)
        data['triad_freq'] = data.groupby('triad_id')['triad_id'].transform('count')
        self.high_freq = list(data[data.triad_freq > self.min_occur].groupby('triad_id').groups.keys())
        return data

    def percent_grouping(self, delta_counts, total):
        max_interval = max(delta_counts, key=delta_counts.get)
        best_window = max_interval
        best_percent = 0.0

        for i in range(max_interval - self.window, max_interval + 1):
            current = sum(delta_counts.get(j, 0) for j in range(i, i + self.window))
            percent = (current / total) * 100
            if percent > best_percent:
                best_percent = percent
                best_window = i + self.window // 2

        return best_window, best_percent

    def find_beacon(self, q_job, result_list):
        while not q_job.empty():
            triad_id = q_job.get()
            with self.l_df:
                df = self.email_data[self.email_data.triad_id == triad_id].copy()

            df[self.timestamp_field] = pd.to_datetime(df[self.timestamp_field])
            df['epoch'] = (df[self.timestamp_field].astype(int) / 1e9).astype(int)
            df = df.sort_values('epoch')
            df['delta'] = df['epoch'].diff().fillna(0)
            df = df[df['delta'] >= self.min_interval]

            delta_counts = dict(df['delta'].value_counts())
            total = sum(delta_counts.values())

            if total > self.min_occur:
                interval, percent = self.percent_grouping(delta_counts, total)
                if percent > self.min_percent:
                    sender = df[self.sender_field].iloc[0]
                    receiver = df[self.receiver_field].iloc[0]
                    size_total = df[self.size_field].sum() if self.size_field in df else 0
                    with self.l_list:
                        result_list.append([sender, receiver, size_total, total, int(percent), interval])

            q_job.task_done()

    def detect_beacons(self, csv_out=None):
        for triad_id in self.high_freq:
            self.q_job.put(triad_id)

        manager = Manager()
        result_list = manager.list()

        processes = [Process(target=self.find_beacon, args=(self.q_job, result_list)) for _ in range(self.threads)]

        for p in processes:
            p.start()
        for p in processes:
            p.join()

        df = pd.DataFrame(list(result_list), columns=self.fields)

        if csv_out:
            self.log(f"Saving results to {csv_out}")
            df.to_csv(csv_out, index=False)

        return df


if __name__ == "__main__":
    detector = EmailBeaconDetector(
        es_index="email-logs-*",
        threads=4,
        verbose=True
    )

    results = detector.detect_beacons(csv_out="email_beaconing.csv")
    print(results.head())
