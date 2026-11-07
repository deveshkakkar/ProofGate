"""Evaluator-owned probe of the packaged pure rule, not the application adapter."""
import json
import sys
sys.path.insert(0, '/app')
from rule import allow
print(json.dumps([allow(**row) for row in json.load(sys.stdin)]))
