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
            "total_tokens": 0,
            "verdicts": {
                "APPROVE": 0,
                "REQUEST_CHANGES": 0,
                "COMMENT": 0
            },
            "severities": {
                "High": 0,
                "Medium": 0,
                "Low": 0
            },
            "vulnerability_types": {
                "SQL Injection": 0,
                "XSS": 0,
                "Broken Auth": 0,
                "Logic Bug": 0,
                "Other": 0
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

    def update_metrics(self, latency: float, verdict: str, severities: Dict[str, int] = None, tokens: int = 0, vulns: Dict[str, int] = None):
        with self._lock:
            self.data["total_prs"] += 1
            self.data["total_latency_sec"] += latency
            self.data["total_tokens"] += tokens
            
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

            # Update vulnerability types
            if vulns:
                for v_type, count in vulns.items():
                    if v_type in self.data["vulnerability_types"]:
                        self.data["vulnerability_types"][v_type] += count
            
            self.save()

    def get_stats(self):
        with self._lock:
            total_prs = self.data["total_prs"]
            avg_latency = self.data["total_latency_sec"] / total_prs if total_prs > 0 else 0
            
            # ROI Calculation: Assume 15 mins saved per PR review
            time_saved_hrs = (total_prs * 15) / 60
            
            return {
                "total_prs_reviewed": total_prs,
                "average_latency_seconds": round(avg_latency, 2),
                "total_tokens_consumed": self.data["total_tokens"],
                "roi_metrics": {
                    "estimated_eng_time_saved_hours": round(time_saved_hrs, 1),
                    "assumed_minutes_per_manual_review": 15
                },
                "verdict_distribution": self.data["verdicts"],
                "security_metrics": {
                    "severity_counts": self.data["severities"],
                    "vulnerability_types": self.data["vulnerability_types"]
                },
                "status": "Operational"
            }

metrics_collector = PRMetrics()
