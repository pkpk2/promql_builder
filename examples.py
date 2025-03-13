from promql_builder import PromQLBuilder

def print_example(name: str, query: str):
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

def run_examples():
    # Basic Examples
    print("\n=== Basic Examples ===")
    
    # Simple metric selection
    query1 = (PromQLBuilder()
        .with_metric("http_requests_total")
        .with_label("status", "200")
        .with_label("method", "GET")
        .build())
    print("Simple metric:", query1)

    # Rate with time window
    query2 = (PromQLBuilder()
        .with_metric("http_requests_total")
        .with_label("status", "500")
        .with_rate("5m")
        .build())
    print("Rate query:", query2)

    # Complex Examples
    print("\n=== Complex Examples ===")

    # Example 1: Aggregation with multiple labels and rate
    complex1 = """sum by (job, instance) (rate(node_cpu_seconds_total{mode!="idle"}[5m]))"""
    builder1 = print_example("CPU Usage by Job and Instance", complex1)
    
    # Modify the query
    if builder1:
        modified1 = (builder1
            .with_label("cpu", "0")
            .with_range("10m")
            .build())
        print("Modified query:", modified1)

    # Example 2: Arithmetic between metrics
    complex2 = """(sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance)) / (count(node_cpu_seconds_total) by (instance)) * 100"""
    print_example("CPU Usage Percentage", complex2)

    # Example 3: Multiple aggregations and filters
    complex3 = """sum by (container) (rate(container_cpu_usage_seconds_total{container!="",pod=~"production-.*"}[5m])) > 0.5"""
    print_example("Container CPU Usage with Threshold", complex3)

    # Example 4: Nested functions and arithmetic
    complex4 = """topk(5, sum by (pod) (rate(container_memory_usage_bytes{container!="POD"}[5m])) / (1024 * 1024))"""
    print_example("Top 5 Memory Usage Pods (MB)", complex4)

    # Example 5: Complex time shifts and offsets
    complex5 = """(sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)) / (sum(rate(http_requests_total[5m] offset 1h)) by (service)) * 100"""
    print_example("Error Rate Change vs 1h Ago", complex5)

    # Programmatic Construction Examples
    print("\n=== Programmatic Construction Examples ===")

    # Complex metric with multiple operations
    complex_builder = (PromQLBuilder()
        .with_metric("container_memory_usage_bytes")
        .with_label("container", "POD", "!=")
        .with_label("namespace", "production")
        .with_rate("5m")
        .with_function("sum", "$expr", by=["pod", "namespace"])
        .with_arithmetic_op("/", 1024 * 1024)  # Convert to MB
        .with_binary_op(">", 100)  # Threshold of 100MB
        .build())
    print("Programmatically built complex query:", complex_builder)

    # Histogram quantile examplepromql_builder_v2.py
    histogram_query = (PromQLBuilder()
        .with_metric("http_request_duration_seconds_bucket")
        .with_label("path", "/api/.*", "=~")
        .with_rate("5m")
        .with_function("histogram_quantile", 0.95, "$expr", by=["path", "method"])
        .build())
    print("95th percentile latency by path:", histogram_query)

    # Multi-stage aggregation
    multi_stage = (PromQLBuilder()
        .with_metric("node_cpu_seconds_total")
        .with_label("mode", "idle", "!=")
        .with_rate("5m")
        .with_function("sum", "$expr", by=["instance"])
        .with_function("topk", 5, "$expr")
        .with_arithmetic_op("*", 100)
        .build())
    print("Top 5 CPU busy instances:", multi_stage)

    # New Examples for v3
    print("\n=== V3-Specific Examples ===")

    # Example with complex label matchers
    complex_labels = """node_cpu_seconds_total{mode=~"user|system",cpu!="0",instance=~".*prod.*"}"""
    print_example("Complex Label Matchers", complex_labels)

    # Example with multiple arithmetic operations
    multi_arithmetic = """(sum(rate(errors[5m])) / sum(rate(requests[5m]))) * 100 + 5"""
    print_example("Multiple Arithmetic Operations", multi_arithmetic)

    # Example with offset and range
    offset_range = """rate(http_requests_total{job="api"}[5m] offset 1h)"""
    print_example("Offset with Range", offset_range)

    # Example with multiple aggregations and grouping
    multi_agg = """max by (job) (sum without (instance) (rate(http_requests_total{code=~"5.."}[5m])))"""
    print_example("Multiple Aggregations with Different Grouping", multi_agg)

    # Advanced Complex Examples
    print("\n=== Advanced Complex Examples ===")

    # Example 1: Alert condition with rate and comparison
    alert_condition = """
    sum(rate(http_requests_total{status=~"5.."}[5m])) 
    / 
    sum(rate(http_requests_total[5m])) 
    > 0.01 and 
    sum(rate(http_requests_total[5m])) > 100
    """
    alert_condition = alert_condition.replace("\n", " ").strip()
    print_example("Complex Alert Condition", alert_condition)

    # Example 2: Predict linear growth with offset comparison
    predict_query = """
    predict_linear(
      node_filesystem_free_bytes{mountpoint="/"}[1h], 
      4 * 3600
    ) < 10 * 1024 * 1024 * 1024
    """
    predict_query = predict_query.replace("\n", " ").strip()
    print_example("Predict Linear Growth", predict_query)

    # Example 3: Multiple aggregations with advanced math
    multi_agg_query = """
    clamp_max(
      sum by (instance) (
        rate(node_cpu_seconds_total{mode!="idle"}[2m])
      ) / on (instance) group_left
      count by (instance) (
        count by (cpu, instance) (node_cpu_seconds_total)
      ),
      1
    )
    """
    multi_agg_query = multi_agg_query.replace("\n", " ").strip()
    print_example("Multiple Aggregations with Normalization", multi_agg_query)

    # Example 4: Histogram bucketing with aggregation
    histogram_complex = """
    histogram_quantile(0.99, 
      sum by (le, service) (
        rate(http_request_duration_seconds_bucket{env="production"}[5m])
      )
    ) > 0.5
    """
    histogram_complex = histogram_complex.replace("\n", " ").strip()
    print_example("Complex Histogram Quantile", histogram_complex)

    # Example 5: Time shift comparison with rate
    time_comp_query = """
    (
      sum by (job) (rate(http_requests_total[5m]))
      -
      sum by (job) (rate(http_requests_total[5m] offset 1d))
    ) 
    / 
    sum by (job) (rate(http_requests_total[5m] offset 1d)) 
    * 100
    """
    time_comp_query = time_comp_query.replace("\n", " ").strip()
    print_example("Time-Shift YoY Comparison", time_comp_query)

    # Modification and Regeneration Examples
    print("\n=== Modification and Regeneration Examples ===")

    # Example 1: Parse, modify and regenerate a complex query
    complex_mod_query = """
    sum by (instance) (
      rate(node_network_receive_bytes_total{device!="lo"}[5m])
    ) > 10 * 1024 * 1024
    """
    complex_mod_query = complex_mod_query.replace("\n", " ").strip()
    builder_mod = print_example("Original Network Traffic Query", complex_mod_query)
    
    if builder_mod:
        # Add additional label filter
        mod1 = (builder_mod
               .with_label("instance", "server-[1-5]", "=~")
               .build())
        print("Modified with instance filter:", mod1)
        
        # Change threshold and add time offset
        mod2 = (builder_mod
               .with_binary_op(">", 100 * 1024 * 1024)  # Increase threshold to 100MB
               .with_offset("1h")                      # Compare with 1 hour ago
               .build())
        print("Modified with threshold and offset:", mod2)
        
        # Add another function
        mod3 = (builder_mod
               .with_function("topk", 3, "$expr")     # Show only top 3 instances
               .build())
        print("Modified with topk function:", mod3)

    # Example 2: Parse, modify and regenerate a histogram query
    histogram_mod_query = """histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))"""
    builder_hist = print_example("Original Histogram Query", histogram_mod_query)
    
    if builder_hist:
        # Change quantile and add label dimensions
        mod1 = (builder_hist
                .with_function("histogram_quantile", 0.99, "$expr", by=["le", "endpoint", "method"])
                .build())
        print("Modified with different quantile and dimensions:", mod1)
        
        # Add threshold comparison
        mod2 = (builder_hist
                .with_binary_op(">", 0.3)  # Alert if 95th percentile > 300ms
                .build())
        print("Modified with threshold:", mod2)

    # Example 3: Parse, modify and regenerate a complex alert query
    alert_mod_query = """
    sum by (job) (rate(errors_total[5m])) 
    / 
    sum by (job) (rate(requests_total[5m])) 
    > 0.01
    """
    alert_mod_query = alert_mod_query.replace("\n", " ").strip()
    builder_alert = print_example("Original Error Rate Alert", alert_mod_query)
    
    if builder_alert:
        # Make alert more sensitive
        mod1 = (builder_alert
                .with_binary_op(">", 0.005)  # More sensitive threshold
                .with_range("10m")          # Longer evaluation window
                .build())
        print("Modified with more sensitive threshold:", mod1)
        
        # Add additional condition
        mod2 = (builder_alert
                .with_label("environment", "production")
                .with_binary_op(">", 0.01)
                .build())
        print("Modified with environment filter:", mod2)

if __name__ == "__main__":
    run_examples() 