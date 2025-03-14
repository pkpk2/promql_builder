#!/usr/bin/env python
from promql_builder import PromQLBuilder

# Test a simple query with labels
query = 'http_requests_total{status="200"}'
builder = PromQLBuilder(query)
rebuilt = builder.build()
print(f"Original: {query}")
print(f"Rebuilt: {rebuilt}")

# Test a sum by query
query = 'sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (job)'
builder = PromQLBuilder(query)
rebuilt = builder.build()
print(f"\nOriginal: {query}")
print(f"Rebuilt: {rebuilt}")

# Test modification
builder.with_label("environment", "production")
modified = builder.build()
print(f"Modified: {modified}") 