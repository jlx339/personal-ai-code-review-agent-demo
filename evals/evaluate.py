"""Score a saved report using expected issues and human labels; no model calls."""
import argparse
import json
from pathlib import Path
from ai_review.schemas import ReviewReport
from ai_review.evaluation import evaluate

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--report',required=True,type=Path)
    p.add_argument('--expected',required=True,type=Path)
    p.add_argument('--labels',required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(evaluate(ReviewReport.from_json(a.report.read_text()),
        json.loads(a.expected.read_text()),json.loads(a.labels.read_text())),indent=2))
