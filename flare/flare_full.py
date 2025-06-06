# coding: utf-8
import sys
import pandas as pd
from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection
from multiprocessing import Process, JoinableQueue, Lock
import time
import warnings
import os
import datetime
import json

warnings.filterwarnings('ignore')

class EmailBeaconDetector:
    """
    Identifies periodic communication patterns in email logs using Elasticsearch.
    Analyzes sender-receiver relationships and email timing patterns.
    """
    def __init__(self,
                 min_occur=10,
                 min_percent=5,
                 window=2,
                 threads=8,
                 period=24,
                 min_interval=2,
                 es_host='localhost',
                 es_port=9200,
                 es_timeout=480,
                 es_index='email-logs-*',
                 kibana_version='4',
                 verbose=True):
        
        # Detection parameters
        self.MIN_OCCURRENCES = min_occur
        self.MIN_PERCENT = min_percent
        self.WINDOW = window
        self.NUM_PROCESSES = threads
        self.period = period
        self.min_interval = min_interval
        
        # Elasticsearch configuration
        self.es_host = es_host
        self.es_port = es_port
        self.es_index = es_index
        self.es_timeout = es_timeout
        self.kibana_version = kibana_version
        
        # Field mappings
        self.sender_field = 'email.sender'
        self.receiver_field = 'email.receiver'
        self.size_field = 'email.size'
        self.timestamp_field = '@timestamp'
        
        self.verbose = verbose
        self._connect_elasticsearch()

    def _connect_elasticsearch(self):
        """Establish Elasticsearch connection"""
        try:
            self.es = Elasticsearch(
                self.es_host,
                port=self.es_port,
                timeout=self.es_timeout,
                verify_certs=False,
                connection_class=RequestsHttpConnection
            )
            if self.verbose:
                print(f"Connected to Elasticsearch at {self.es_host}:{self.es_port}")
        except Exception as e:
            raise ConnectionError(f"Elasticsearch connection failed: {str(e)}")

    def _build_query(self, hours):
        """Construct Elasticsearch query for email data"""
        now = int(time.time() * 1000)
        timeframe = now - (hours * 60 * 60 * 1000)

        return {
            "query": {
                "bool": {
                    "must": [{
                        "range": {
                            self.timestamp_field: {
                                "gte": timeframe,
                                "lte": now,
                                "format": "epoch_millis"
                            }
                        }
                    }],
                    "filter": [
                        {"exists": {"field": self.sender_field}},
                        {"exists": {"field": self.receiver_field}}
                    ]
                }
            },
            "_source": [self.sender_field, self.receiver_field, 
                       self.size_field, self.timestamp_field]
        }

    def _calculate_intervals(self, data):
        """Calculate time intervals between consecutive emails"""
        data = data.sort_values(self.timestamp_field)
        data['delta'] = (data[self.timestamp_field] - 
                        data[self.timestamp_field].shift()).fillna(0)
        return data[1:]  # Skip first row with NaN delta

    def detect_beacons(self):
        """Main detection workflow"""
        # Execute ES query
        response = helpers.scan(
            client=self.es,
            query=self._build_query(self.period),
            index=self.es_index,
            timeout="10m"
        )
        
        # Process results
        df = pd.json_normalize([hit['_source'] for hit in response])
        if df.empty:
            raise ValueError("No email data found in specified index")
            
        # Create unique communication pairs
        df['pair_id'] = (df[self.sender_field] + 
                        df[self.receiver_field]).apply(hash)
        df['pair_freq'] = df.groupby('pair_id')['pair_id'].transform('count')
        
        # Filter frequent pairs
        frequent_pairs = df[df.pair_freq > self.MIN_OCCURRENCES]
        return self._analyze_temporal_patterns(frequent_pairs)

    def _analyze_temporal_patterns(self, data):
        """Analyze temporal patterns for frequent email pairs"""
        results = []
        
        for pair_id, group in data.groupby('pair_id'):
            timed_data = self._calculate_intervals(group)
            intervals = timed_data['delta'].value_counts().to_dict()
            
            # Filter short intervals
            intervals = {k:v for k,v in intervals.items() 
                        if k >= self.min_interval}
            
            total = sum(intervals.values())
            if total < self.MIN_OCCURRENCES:
                continue
                
            # Calculate pattern metrics
            interval, confidence = self._calculate_pattern_confidence(intervals, total)
            if confidence >= self.MIN_PERCENT:
                results.append({
                    'sender': group[self.sender_field].iloc[0],
                    'receiver': group[self.receiver_field].iloc[0],
                    'total_emails': total,
                    'average_size': group[self.size_field].mean(),
                    'detected_interval': interval,
                    'confidence': f"{confidence:.1f}%"
                })
        
        return pd.DataFrame(results)

    def _calculate_pattern_confidence(self, intervals, total):
        """Calculate pattern confidence using sliding window"""
        max_confidence = 0
        best_interval = 0
        
        for window_start in range(min(intervals.keys()), max(intervals.keys())):
            window_end = window_start + self.WINDOW
            window_count = sum(v for k,v in intervals.items() 
                             if window_start <= k <= window_end)
            
            confidence = (window_count / total) * 100
            if confidence > max_confidence:
                max_confidence = confidence
                best_interval = (window_start + window_end) // 2
                
        return best_interval, max_confidence

if __name__ == "__main__":
    detector = EmailBeaconDetector(
        min_occur=15,
        min_percent=30,
        period=48
    )

    results = detector.detect_beacons()
    print(results[['sender', 'receiver', 'detected_interval', 'confidence']])
