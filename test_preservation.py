#!/usr/bin/env python3
"""
PromQL Builder Parameter Preservation Test
This script tests that parameters are preserved when modifying parsed queries.
"""

from promql_builder import PromQLBuilder

def print_test_result(test_name, original_query, rebuilt_query, modified_query):
    """Print the results of a parameter preservation test."""
    print(f"\n=== Test: {test_name} ===")
    print(f"Original query: {original_query}")
    print(f"Rebuilt without modifications: {rebuilt_query}")
    print(f"Modified query: {modified_query}")

def run_tests():
    """Run tests to verify parameter preservation."""
    print("PromQL Builder Parameter Preservation Tests")
    print("==========================================")
    
    # Test 1: Simple Query
    original = "http_requests_total{status=\"200\"}"
    builder = PromQLBuilder(original)
    rebuilt = builder.build()
    modified = (builder
        .with_label("method", "GET")
        .with_label("environment", "production")
        .build())
    print_test_result("Simple Query with Labels", original, rebuilt, modified)
    
    # Test 2: Rate Query
    original = "rate(http_requests_total{status=\"500\"}[5m])"
    builder = PromQLBuilder(original)
    rebuilt = builder.build()
    modified = (builder
        .with_range("10m")
        .with_label("environment", "production")
        .build())
    print_test_result("Rate Query", original, rebuilt, modified)
    
    # Test 3: Complex Query with Aggregation
    original = "sum(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) by (job)"
    builder = PromQLBuilder(original)
    rebuilt = builder.build()
    modified = (builder
        .with_function("sum", "$expr", by=["job", "instance"])
        .with_binary_op(">", 0.5)
        .build())
    print_test_result("Aggregation with Grouping", original, rebuilt, modified)
    
    # Test 4: Query with Binary Operator
    original = "(sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))) * 100 > 5"
    builder = PromQLBuilder(original)
    rebuilt = builder.build()
    modified = (builder
        .with_label("method", "GET")
        .with_binary_op(">", 1)  # Change threshold
        .build())
    print_test_result("Complex Query with Binary Operator", original, rebuilt, modified)
    
if __name__ == "__main__":
    run_tests() 