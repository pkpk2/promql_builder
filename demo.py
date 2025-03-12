#!/usr/bin/env python3
"""
PromQL Builder Demo
This script demonstrates the main features of the PromQL Builder library.
"""

from promql_builder import PromQLBuilder

def print_demo(name, query):
    """Print a demo query with name and resulting PromQL."""
    print(f"\n=== {name} ===")
    print(f"PromQL: {query}")

def run_demo():
    """Run the PromQL Builder demonstration."""
    print("PromQL Builder Demonstration")
    print("===========================")
    
    # Basic metric selection
    basic_query = (PromQLBuilder()
        .with_metric("http_requests_total")
        .with_label("status", "200")
        .with_label("method", "GET")
        .build())
    print_demo("Basic Metric Selection", basic_query)
    
    # Rate function with time window
    rate_query = (PromQLBuilder()
        .with_metric("http_requests_total")
        .with_label("status", "5..", "=~")
        .with_rate("5m")
        .build())
    print_demo("Rate Function", rate_query)
    
    # Aggregation with grouping
    agg_query = (PromQLBuilder()
        .with_metric("node_cpu_seconds_total")
        .with_label("mode", "idle", "!=")
        .with_rate("5m")
        .with_function("sum", "$expr", by=["instance", "job"])
        .build())
    print_demo("Aggregation with Grouping", agg_query)
    
    # Arithmetic operations
    arith_query = (PromQLBuilder()
        .with_metric("node_memory_MemFree_bytes")
        .with_arithmetic_op("/", 1024 * 1024 * 1024)  # Convert to GB
        .build())
    print_demo("Arithmetic Operation", arith_query)
    
    # Binary comparison
    binary_query = (PromQLBuilder()
        .with_metric("node_filesystem_avail_bytes")
        .with_label("mountpoint", "/")
        .with_arithmetic_op("/", "node_filesystem_size_bytes{mountpoint=\"/\"}")
        .with_arithmetic_op("*", 100)
        .with_binary_op("<", 10)  # Less than 10% free
        .build())
    print_demo("Binary Comparison", binary_query)
    
    # Complex function - Histogram Quantile
    hist_query = (PromQLBuilder()
        .with_metric("http_request_duration_seconds_bucket")
        .with_rate("5m")
        .with_function("histogram_quantile", 0.95, "$expr", by=["method", "path"])
        .build())
    print_demo("Histogram Quantile", hist_query)
    
    # Parse and modify an existing query
    original = "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (job)"
    print(f"\n=== Parse and Modify Query ===")
    print(f"Original: {original}")
    
    builder = PromQLBuilder(original)
    modified = (builder
        .with_label("method", "GET")
        .with_range("10m")  # Change time window
        .with_binary_op(">", 100)  # Add threshold
        .build())
    print(f"Modified: {modified}")

if __name__ == "__main__":
    run_demo() 