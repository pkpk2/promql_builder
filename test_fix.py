#!/usr/bin/env python3
"""Test script for PromQLBuilder fixes."""

from promql_builder import PromQLBuilder

# Test cases that should be fixed by our changes
test_cases = [
    # Simple query with labels
    "http_requests_total{status=\"200\"}",
    # Multiple labels
    "http_requests_total{status=\"200\",method=\"GET\"}",
    # Rate function
    "rate(http_requests_total{status=\"500\"}[5m])",
    # Sum by
    "sum(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) by (job)",
    # Sum by (alternative format)
    "sum by (job) (rate(http_requests_total[5m]))"
]

for i, query in enumerate(test_cases):
    print(f"\nTest Case {i+1}: {query}")
    builder = PromQLBuilder(query)
    rebuilt = builder.build()
    print(f"Rebuilt: {rebuilt}")
    
    # Also test that modifications work
    builder.with_label("environment", "production")
    if i == 2:  # For the rate query, also test changing the range
        builder.with_range("10m")
    modified = builder.build()
    print(f"Modified: {modified}") 