#!/usr/bin/env python3
"""Example demonstrating practical uses of the clone method."""

from promql_builder import PromQLBuilder

def practical_clone_example():
    """Demonstrate a practical use case for cloning builders."""
    print("PromQLBuilder Clone Method - Practical Example")
    print("=============================================")
    
    # Create a base query template that will be used for multiple similar queries
    base_query = (PromQLBuilder()
        .with_metric("istio_requests_total")
        .with_label("service_namespace", "adm")
        .with_label("service_name", "adm-store")
        .with_rate("5m"))
    
    print(f"Base query: {base_query.build()}")
    print("\nDeriving multiple specialized queries from the base query:")
    
    # Create different views for different environments
    environments = ["production", "staging", "development"]
    env_queries = {}
    
    for env in environments:
        # Clone the base query and add environment-specific parameters
        env_builder = base_query.clone()
        env_builder.with_label("environment", env)
        env_queries[env] = env_builder
        print(f"  {env}: {env_builder.build()}")
    
    # Make a more complex production query with error rate calculation
    error_rate = env_queries["production"].clone()
    error_rate.with_label("response_code", "5..", "=~")  # 5xx errors
    error_rate.with_function("sum", "$expr", by=["service_name"])
    
    # Create a total requests query
    total_requests = env_queries["production"].clone()
    total_requests.with_function("sum", "$expr", by=["service_name"])
    
    # Calculate error percentage using a direct expression
    error_percentage_expr = f"({error_rate.build()} / {total_requests.build()}) * 100 > 1"
    
    # Create the calculation: (error_rate / total_requests) * 100 > 1
    error_percentage = PromQLBuilder()
    error_percentage.with_metric("expr")  # Using a placeholder metric
    # Set full_expression directly for this special case
    error_percentage.full_expression = error_percentage_expr
    
    print("\nComplex derived queries:")
    print(f"  Error rate: {error_rate.build()}")
    print(f"  Total requests: {total_requests.build()}")
    print(f"  Error percentage with threshold: {error_percentage_expr}")
    
    # Latency monitoring - clone the base production query again
    latency = env_queries["production"].clone()
    latency.with_metric("istio_request_duration_milliseconds")
    latency.with_function("histogram_quantile", 0.95, "$expr", by=["service_name"])
    latency.with_binary_op(">", 500)  # Alert if 95th percentile latency > 500ms
    
    print(f"  Latency monitoring: {latency.build()}")

if __name__ == "__main__":
    practical_clone_example() 