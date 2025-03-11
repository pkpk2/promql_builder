from promql_builder_v2 import PromQLBuilder, MetricSelector, LabelMatcher

def print_example(name: str, query: str):
    print(f"\n=== {name} ===")
    print(f"Original query: {query}")
    builder = PromQLBuilder(query)
    rebuilt = builder.build()
    print(f"Rebuilt query:  {rebuilt}")
    return builder

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
    complex1 = """
    sum by (job, instance) (
        rate(node_cpu_seconds_total{mode!="idle"}[5m])
    )
    """
    builder1 = print_example("CPU Usage by Job and Instance", complex1)
    
    # Modify the query
    modified1 = (builder1
        .with_label("cpu", "0")
        .with_range("10m")
        .build())
    print("Modified query:", modified1)

    # Example 2: Arithmetic between metrics
    complex2 = """
    (
        sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance)
    ) / (
        count(node_cpu_seconds_total) by (instance)
    ) * 100
    """
    print_example("CPU Usage Percentage", complex2)

    # Example 3: Multiple aggregations and filters
    complex3 = """
    sum by (container) (
        rate(container_cpu_usage_seconds_total{
            container!="",
            pod=~"production-.*"
        }[5m])
    ) > 0.5
    """
    print_example("Container CPU Usage with Threshold", complex3)

    # Example 4: Nested functions and arithmetic
    complex4 = """
    topk(5,
        sum by (pod) (
            rate(container_memory_usage_bytes{container!="POD"}[5m])
        ) / (1024 * 1024)
    )
    """
    print_example("Top 5 Memory Usage Pods (MB)", complex4)

    # Example 5: Complex time shifts and offsets
    complex5 = """
    (
        sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
    ) / (
        sum(rate(http_requests_total[5m] offset 1h)) by (service)
    ) * 100
    """
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

    # Histogram quantile example
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

if __name__ == "__main__":
    run_examples() 