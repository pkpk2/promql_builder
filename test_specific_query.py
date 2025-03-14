#!/usr/bin/env python3
"""Test the specific query from the user's question."""

from promql_builder import PromQLBuilder

# The exact query from the user's question
query = "sum(rate(istio_requests_total{cloud_region='eastus2', service_namespace='adm', service_name='adm-store'}[5m])) by (response_code)"

print(f"Original query: {query}")

# Parse and rebuild
builder = PromQLBuilder(query)
rebuilt = builder.build()
print(f"Rebuilt query: {rebuilt}")

# Make modifications to demonstrate it works correctly
builder.with_label("environment", "production")
builder.with_range("10m")
modified = builder.build()
print(f"Modified query: {modified}")

# Test removing a label
builder.remove_label("service_namespace")
removed_label = builder.build()
print(f"After removing service_namespace: {removed_label}")

# Test changing the by clause
# First remove the existing sum function 
original_functions = builder.functions.copy()
builder.functions = [f for f in builder.functions if f.name != "sum"]
# Then add it back with different grouping
builder.with_function("sum", "$expr", by=["response_code", "method"])
changed_grouping = builder.build()
print(f"After changing grouping: {changed_grouping}")

# Reset functions and add a binary operator
builder.functions = original_functions
builder.with_binary_op(">", 0)
with_threshold = builder.build()
print(f"With threshold added: {with_threshold}") 