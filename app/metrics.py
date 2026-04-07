import json
import os
import threading
from typing import Dict

METRICS_FILE = "metrics.json"

class PRMetrics:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PRMetrics, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.data = {
            "total_prs": 0,
            "total_latency_sec": 0.0,
            "verdicts": {
                "APPROVE": 0,
                "REQUEST_CHANGES": 0,
                "COMMENT": 0
            },
            "severities": {
                "High": 0,
                "Medium": 0,
                "Low": 0
            }
        }
        self.load()

    def load(self):
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, 'r') as f:
                    self.data.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass # Use defaults if file is corrupted

    def save(self):
        try:
            with open(METRICS_FILE, 'w') as f:
                json.dump(self.data, f, indent=4)
        except IOError:
            pass

    def update_metrics(self, latency: float, verdict: str, severities: Dict[str, int] = None):
        with self._lock:
            self.data["total_prs"] += 1
            self.data["total_latency_sec"] += latency
            
            # Update verdict count
            if verdict in self.data["verdicts"]:
                self.data["verdicts"][verdict] += 1
            else:
                self.data["verdicts"]["COMMENT"] += 1

            # Update severity counts
            if severities:
                for sev, count in severities.items():
                    if sev in self.data["severities"]:
                        self.data["severities"][sev] += count
            
            self.save()

    def get_stats(self):
        with self._lock:
            avg_latency = self.data["total_latency_sec"] / self.data["total_prs"] if self.data["total_prs"] > 0 else 0
            return {
                "total_prs_reviewed": self.data["total_prs"],
                "average_latency_seconds": round(avg_latency, 2),
                "verdict_distribution": self.data["verdicts"],
                "severity_counts": self.data["severities"],
                "status": "Operational"
            }

metrics_collector = PRMetrics()
