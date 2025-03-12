from promql_builder import PromQLBuilder

def test_query(name: str, query: str):
    print(f"\n=== {name} ===")
    print(f"Original query: {query}")
    try:
        builder = PromQLBuilder(query)
        rebuilt = builder.build()
        print(f"Rebuilt query:  {rebuilt}")
        return builder
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def run_tests():
    # Basic Queries
    print("\n=== Basic Queries ===")
    
    # Simple metric
    test_query("Simple Metric", 'http_requests_total')
    
    # Metric with labels
    test_query("Metric with Labels", 'http_requests_total{status="200",method="GET"}')
    
    # Rate with time window
    test_query("Rate Query", 'rate(http_requests_total{status="500"}[5m])')
    
    # Complex Queries
    print("\n=== Complex Queries ===")
    
    # Aggregation with multiple labels
    test_query(
        "Aggregation with Labels",
        'sum by (job, instance) (rate(node_cpu_seconds_total{mode!="idle"}[5m]))'
    )
    
    # Nested functions
    test_query(
        "Nested Functions",
        'sum(rate(http_requests_total{code=~"5.."}[5m])) by (service)'
    )
    
    # Arithmetic between metrics
    test_query(
        "Arithmetic Operations",
        '(sum(rate(errors[5m])) / sum(rate(requests[5m]))) * 100'
    )
    
    # Multiple aggregations and filters
    test_query(
        "Multiple Aggregations",
        'sum by (container) (rate(container_cpu_usage_seconds_total{container!="",pod=~"production-.*"}[5m])) > 0.5'
    )
    
    # Query Modifications
    print("\n=== Query Modifications ===")
    
    # Modify existing query
    query = 'rate(http_requests_total{status="200"}[5m])'
    builder = test_query("Original Query", query)
    
    if builder:
        # Add label and change window
        modified = (builder
            .with_label("path", "/api", "=~")
            .with_range("10m")
            .build())
        print(f"Modified query: {modified}")
        
        # Add function and threshold
        modified = (builder
            .with_function("sum", "$expr", by=["path"])
            .with_binary_op(">", 100)
            .build())
        print(f"Modified with function: {modified}")
        
        # Remove labels and add arithmetic
        modified = (builder
            .remove_label("status")
            .with_arithmetic_op("*", 2)
            .build())
        print(f"Modified with arithmetic: {modified}")

    # Advanced Queries
    print("\n=== Advanced Queries ===")
    
    # Histogram quantile
    test_query(
        "Histogram Quantile",
        'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))'
    )
    
    # Complex time shifts
    test_query(
        "Time Shifts",
        'sum(rate(http_requests_total{status=~"5.."}[5m] offset 1h)) by (service)'
    )
    
    # Multiple binary operations
    test_query(
        "Multiple Binary Ops",
        'sum(rate(errors[5m])) / sum(rate(requests[5m])) > 0.01 and sum(rate(requests[5m])) > 100'
    )

    # Error Cases
    print("\n=== Error Cases ===")
    
    # Invalid metric name
    test_query("Invalid Metric", '123invalid{label="value"}')
    
    # Mismatched brackets
    test_query("Mismatched Brackets", 'metric{label="value"')
    
    # Invalid duration
    test_query("Invalid Duration", 'rate(metric[5z])')

if __name__ == "__main__":
    run_tests() 