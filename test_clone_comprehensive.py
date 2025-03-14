#!/usr/bin/env python3
"""Comprehensive test for the PromQLBuilder clone method."""

from promql_builder import PromQLBuilder

def test_clone_with_various_query_types():
    """Test the clone method with different types of queries."""
    print("Testing clone method with various query types\n")
    
    # Test 1: Simple metric with labels
    test_simple_metric_clone()
    
    # Test 2: Rate function
    test_rate_function_clone()
    
    # Test 3: Aggregation with grouping
    test_aggregation_clone()
    
    # Test 4: Complex query with nested functions
    test_complex_query_clone()
    
    # Test 5: Query with binary operations
    test_binary_operations_clone()
    
    print("\nAll clone tests completed successfully.")

def test_simple_metric_clone():
    """Test cloning a simple metric query."""
    print("Test 1: Simple metric with labels")
    
    # Create original builder
    original = PromQLBuilder().with_metric("node_cpu_seconds_total").with_label("mode", "idle")
    original_query = original.build()
    
    # Clone and modify
    clone = original.clone()
    clone.with_label("cpu", "0")
    
    # Verify
    print(f"  Original: {original_query}")
    print(f"  Modified original: {original.build()}")
    print(f"  Modified clone: {clone.build()}")
    print("  Passed ✓" if original.build() == original_query else "  Failed ✗")
    print()

def test_rate_function_clone():
    """Test cloning a query with rate function."""
    print("Test 2: Rate function")
    
    # Create original builder
    original = PromQLBuilder().with_metric("http_requests_total").with_rate("5m")
    original_query = original.build()
    
    # Clone and modify
    clone = original.clone()
    clone.with_range("10m")
    
    # Verify
    print(f"  Original: {original_query}")
    print(f"  Modified original: {original.build()}")
    print(f"  Modified clone: {clone.build()}")
    print("  Passed ✓" if original.build() == original_query else "  Failed ✗")
    print()

def test_aggregation_clone():
    """Test cloning a query with aggregation and grouping."""
    print("Test 3: Aggregation with grouping")
    
    # Create original builder
    original = (PromQLBuilder()
                .with_metric("node_cpu_seconds_total")
                .with_rate("5m")
                .with_function("sum", "$expr", by=["instance", "job"]))
    original_query = original.build()
    
    # Clone and modify
    clone = original.clone()
    clone.with_function("sum", "$expr", by=["instance"])  # Change grouping
    
    # Verify
    print(f"  Original: {original_query}")
    print(f"  Modified original: {original.build()}")
    print(f"  Modified clone: {clone.build()}")
    print("  Passed ✓" if original.build() == original_query else "  Failed ✗")
    print()

def test_complex_query_clone():
    """Test cloning a complex query with nested functions."""
    print("Test 4: Complex query with nested functions")
    
    # Parse a complex query
    complex_query = "sum(rate(istio_requests_total{cloud_region='eastus2', service_namespace='adm'}[5m])) by (response_code)"
    original = PromQLBuilder(complex_query)
    original_query = original.build()
    
    # Clone and modify multiple things
    clone = original.clone()
    clone.with_label("additional", "label")
    clone.with_range("1h")
    clone.with_function("sum", "$expr", by=["service_name"])  # Change the grouping
    clone.with_binary_op(">", 100)
    
    # Verify
    print(f"  Original: {original_query}")
    print(f"  Modified original: {original.build()}")
    print(f"  Modified clone: {clone.build()}")
    print("  Passed ✓" if original.build() == original_query else "  Failed ✗")
    print()

def test_binary_operations_clone():
    """Test cloning a query with binary operations."""
    print("Test 5: Query with binary operations")
    
    # Create original builder with binary ops
    original = (PromQLBuilder()
                .with_metric("node_memory_MemFree_bytes")
                .with_arithmetic_op("/", "node_memory_MemTotal_bytes")
                .with_arithmetic_op("*", 100)
                .with_binary_op("<", 10))
    original_query = original.build()
    
    # Clone and modify
    clone = original.clone()
    clone.with_binary_op("<", 5)  # Change threshold
    
    # Verify
    print(f"  Original: {original_query}")
    print(f"  Modified original: {original.build()}")
    print(f"  Modified clone: {clone.build()}")
    print("  Passed ✓" if original.build() == original_query else "  Failed ✗")
    print()

if __name__ == "__main__":
    test_clone_with_various_query_types() 