#!/usr/bin/env python3
"""
PromQL Analyzer Example

This script demonstrates how to use the PromQLBuilder class to analyze and modify PromQL queries.
It shows practical examples of inspecting queries, extracting information, and making changes.
"""

from promql_builder import PromQLBuilder
import json

def analyze_query(query_string):
    """Analyze a PromQL query and print detailed information about it."""
    builder = PromQLBuilder(query_string)
    info = builder.get_query_info()
    
    print(f"\n--- Analysis of query: {query_string} ---\n")
    
    # Basic query components
    print(f"Metric name: {info['metric_name']}")
    
    # Labels
    if info['labels']:
        print("\nLabels:")
        for label in info['labels']:
            print(f"  {label['name']} {label['operator']} \"{label['value']}\"")
    else:
        print("\nNo labels specified")
    
    # Range window and offset
    if info['range_window']:
        print(f"\nRange window: [{info['range_window']}]")
    
    if info['offset']:
        print(f"Offset: {info['offset']}")
    
    # Functions
    if info['functions']:
        print("\nFunctions:")
        for func in info['functions']:
            func_str = f"  {func['name']}({', '.join(func['args'])})"
            if func['group_by']:
                func_str += f" by ({', '.join(func['group_by'])})"
            elif func['without']:
                func_str += f" without ({', '.join(func['without'])})"
            print(func_str)
    
    # Operations
    if info['arithmetic_ops']:
        print("\nArithmetic operations:")
        for op in info['arithmetic_ops']:
            print(f"  {op['operator']} {op['value']}")
    
    if info['binary_ops']:
        print("\nBinary operations:")
        for op in info['binary_ops']:
            print(f"  {op['operator']} {op['value']}")
    
    print(f"\nFull built query: {info['full_query']}")
    print("\n" + "-"*50)

def modify_query_example():
    """Example of modifying an existing query and comparing before/after."""
    original_query = 'sum(rate(http_requests_total{status=~"5.."}[5m])) by (instance) > 5'
    print(f"\n--- Modifying Query Example ---\n")
    print(f"Original query: {original_query}")
    
    # Parse the original query
    builder = PromQLBuilder(original_query)
    
    # Extract and display current settings
    print("\nCurrent settings:")
    print(f"  Metric: {builder.get_metric_name()}")
    print(f"  Labels: {json.dumps(builder.get_labels(), indent=2)}")
    print(f"  Range window: {builder.get_range_window()}")
    print(f"  Functions: {json.dumps(builder.get_functions(), indent=2)}")
    print(f"  Binary ops: {json.dumps(builder.get_binary_ops(), indent=2)}")
    
    # Modify the query
    # 1. Change the status label to be more specific
    builder.remove_label("status")
    builder.with_label("status", "500", "=")
    
    # 2. Add an environment label
    builder.with_label("environment", "production")
    
    # 3. Change the range window from 5m to 10m
    builder.with_range("10m")
    
    # 4. Add a division operation to calculate per-second rate
    builder.with_arithmetic_op("/", 60)
    
    # 5. Change the threshold from > 5 to > 1
    builder.remove_binary_op()
    builder.with_binary_op(">", 1)
    
    # Get the modified query
    modified_query = builder.build()
    
    # Extract and display new settings
    print("\nModified settings:")
    new_info = builder.get_query_info()
    print(f"  Metric: {new_info['metric_name']}")
    print(f"  Labels: {json.dumps(new_info['labels'], indent=2)}")
    print(f"  Range window: {new_info['range_window']}")
    print(f"  Functions: {json.dumps(new_info['functions'], indent=2)}")
    print(f"  Arithmetic ops: {json.dumps(new_info['arithmetic_ops'], indent=2)}")
    print(f"  Binary ops: {json.dumps(new_info['binary_ops'], indent=2)}")
    
    print(f"\nModified query: {modified_query}")
    print("\n" + "-"*50)

def extract_alert_conditions():
    """Example of extracting alerting conditions from queries."""
    alert_queries = [
        'http_requests_total > 1000',
        'rate(errors_total[5m]) / rate(requests_total[5m]) > 0.01',
        'sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) > 5',
        'count(up == 0) > 1',
        'avg_over_time(cpu_usage[1h]) > 90'
    ]
    
    print("\n--- Extracting Alert Conditions ---\n")
    print("Alert conditions extracted from queries:")
    
    for query in alert_queries:
        builder = PromQLBuilder(query)
        info = builder.get_query_info()
        
        metric = info['metric_name'] or "unknown_metric"
        
        # Get the binary operation (threshold)
        if info['binary_ops']:
            op = info['binary_ops'][0]
            threshold = op['value']
            operator = op['operator']
            
            # Get any labels that might define the scope
            labels_scope = []
            for label in info['labels']:
                labels_scope.append(f"{label['name']}={label['value']}")
            
            # Get any grouping from functions
            grouping = []
            for func in info['functions']:
                if func['group_by']:
                    grouping = func['group_by']
            
            # Construct a human-readable alert description
            alert_desc = f"Alert: {metric}"
            if labels_scope:
                alert_desc += f" with {', '.join(labels_scope)}"
            alert_desc += f" {operator} {threshold}"
            if grouping:
                alert_desc += f" grouped by {', '.join(grouping)}"
            
            print(f"\n- Query: {query}")
            print(f"  {alert_desc}")
        else:
            print(f"\n- Query: {query}")
            print("  No alert condition found")
    
    print("\n" + "-"*50)

def build_dashboard_queries():
    """Example of building a set of queries for a dashboard."""
    print("\n--- Building Dashboard Queries ---\n")
    print("Creating a set of queries for a monitoring dashboard:")
    
    # Base metric for HTTP requests
    http_base = PromQLBuilder()
    http_base.with_metric("http_requests_total")
    
    # 1. Query for total requests by endpoint
    requests_by_endpoint = PromQLBuilder()
    requests_by_endpoint.with_metric("http_requests_total")
    requests_by_endpoint.with_range("5m")
    requests_by_endpoint.with_function("rate", "$expr")
    requests_by_endpoint.with_function("sum", "$expr", by=["endpoint"])
    
    # 2. Query for error rate percentage
    error_rate = PromQLBuilder()
    error_rate.with_metric("http_requests_total")
    error_rate.with_label("status", "5..", "=~")
    error_rate.with_range("5m")
    error_rate.with_function("rate", "$expr")
    error_rate.with_function("sum", "$expr")
    error_rate.with_arithmetic_op("/", "sum(rate(http_requests_total[5m]))")
    error_rate.with_arithmetic_op("*", 100)
    
    # 3. Query for 95th percentile response time
    response_time = PromQLBuilder()
    response_time.with_metric("http_request_duration_seconds")
    response_time.with_range("5m")
    response_time.with_function("histogram_quantile", 0.95, "rate($expr)")
    
    # Print out the queries and their structure
    dashboard_queries = [
        ("Requests by Endpoint", requests_by_endpoint),
        ("Error Rate (%)", error_rate),
        ("95th Percentile Response Time", response_time)
    ]
    
    for title, builder in dashboard_queries:
        print(f"\n{title}:")
        info = builder.get_query_info()
        print(f"  Query: {info['full_query']}")
        
        # Print key components
        print("  Components:")
        print(f"    - Metric: {info['metric_name']}")
        if info['labels']:
            labels_str = ", ".join([f"{l['name']}{l['operator']}\"{l['value']}\"" for l in info['labels']])
            print(f"    - Labels: {labels_str}")
        if info['functions']:
            funcs_str = ", ".join([f"{f['name']}()" for f in info['functions']])
            print(f"    - Functions: {funcs_str}")
    
    print("\n" + "-"*50)

def demonstrate_deduplication():
    """Demonstrate how deduplication works for labels and functions."""
    print("\n--- Demonstrating Deduplication ---\n")
    
    # Create a basic query
    builder = PromQLBuilder()
    builder.with_metric("http_requests_total")
    builder.with_label("status", "200")
    builder.with_label("method", "GET")
    builder.with_function("rate", "$expr")
    
    # Print the initial query
    initial_query = builder.build()
    initial_info = builder.get_query_info()
    print(f"Initial query: {initial_query}")
    print(f"Initial labels: {json.dumps(initial_info['labels'], indent=2)}")
    print(f"Initial functions: {json.dumps(initial_info['functions'], indent=2)}")
    
    # Now modify the same label and function
    print("\nModifying existing label and function...")
    builder.with_label("status", "500")  # Change status from 200 to 500
    builder.with_function("rate", "$expr", by=["method"])  # Add a 'by' clause to rate
    
    # Print the updated query
    modified_query = builder.build()
    modified_info = builder.get_query_info()
    print(f"Modified query: {modified_query}")
    print(f"Modified labels: {json.dumps(modified_info['labels'], indent=2)}")
    print(f"Modified functions: {json.dumps(modified_info['functions'], indent=2)}")
    
    # Add a new label and function
    print("\nAdding new label and function...")
    builder.with_label("path", "/api", "=~")
    builder.with_function("sum", "$expr", by=["instance"])
    
    # Print the final query
    final_query = builder.build()
    final_info = builder.get_query_info()
    print(f"Final query: {final_query}")
    print(f"Final labels: {json.dumps(final_info['labels'], indent=2)}")
    print(f"Final functions: {json.dumps(final_info['functions'], indent=2)}")
    
    print("\nNote how the 'status' label was updated rather than duplicated,")
    print("and the 'rate' function was updated with a grouping clause.")
    
    print("\n" + "-"*50)

if __name__ == "__main__":
    # Demo all examples
    example_queries = [
        'http_requests_total{status="200"}',
        'rate(node_cpu_seconds_total{mode="idle"}[5m])',
        'sum(rate(http_requests_total{code=~"5.."}[5m])) by (service)',
        'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))',
        'node_memory_MemFree_bytes / node_memory_MemTotal_bytes * 100 < 10'
    ]
    
    for query in example_queries:
        analyze_query(query)
    
    modify_query_example()
    extract_alert_conditions()
    build_dashboard_queries()
    demonstrate_deduplication() 