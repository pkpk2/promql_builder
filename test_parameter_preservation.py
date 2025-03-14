#!/usr/bin/env python3
"""
Test script to verify that PromQLBuilder preserves all parameters when modifying queries.
This validates that the builder properly rebuilds queries from its internal state
rather than returning the original query string.
"""

from promql_builder import PromQLBuilder

def test_query_preservation(original_query, description, modifications=None):
    """Test that query parameters are preserved when modifying and rebuilding a query."""
    print(f"\n=== Testing {description} ===")
    print(f"Original query: {original_query}")
    
    # Create builder from original query
    builder = PromQLBuilder(original_query)
    
    # Print the parsed query information
    print("\nParsed query information:")
    query_info = builder.get_query_info()
    print(f"  Metric name: {query_info['metric_name']}")
    print(f"  Labels: {query_info['labels']}")
    print(f"  Range window: {query_info['range_window']}")
    print(f"  Functions: {[f['name'] for f in query_info['functions']]}")
    print(f"  Binary ops: {query_info['binary_ops']}")
    print(f"  Arithmetic ops: {query_info['arithmetic_ops']}")
    
    # Rebuild the query without modifications
    rebuilt = builder.build()
    print(f"\nRebuilt without modifications: {rebuilt}")
    
    # Apply modifications if specified
    if modifications:
        for mod_func, args, kwargs in modifications:
            method = getattr(builder, mod_func)
            method(*args, **kwargs)
        
        # Get updated info and rebuilt query
        modified_info = builder.get_query_info()
        modified_query = builder.build()
        
        print("\nAfter modifications:")
        print(f"  Metric name: {modified_info['metric_name']}")
        print(f"  Labels: {modified_info['labels']}")
        print(f"  Range window: {modified_info['range_window']}")
        print(f"  Functions: {[f['name'] for f in modified_info['functions']]}")
        print(f"  Binary ops: {modified_info['binary_ops']}")
        print(f"  Arithmetic ops: {modified_info['arithmetic_ops']}")
        print(f"  Modified query: {modified_query}")
    
    return builder

def run_tests():
    """Run a series of tests with different query types and modifications."""
    
    # Test 1: Simple metric with labels
    test_query_preservation(
        'http_requests_total{status="200"}',
        "Simple metric with labels",
        [
            ('with_label', ['method', 'GET'], {}),
            ('with_label', ['environment', 'production'], {})
        ]
    )
    
    # Test 2: Rate function
    test_query_preservation(
        'rate(http_requests_total{status="500"}[5m])',
        "Rate function",
        [
            ('with_range', ['10m'], {}),
            ('with_label', ['environment', 'production'], {})
        ]
    )
    
    # Test 3: Aggregation with grouping
    test_query_preservation(
        'sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (job)',
        "Aggregation with grouping",
        [
            ('with_function', ['sum', '$expr'], {'by': ['job', 'instance']}),
            ('with_binary_op', ['>', 0.5], {})
        ]
    )
    
    # Test 4: Arithmetic operation
    test_query_preservation(
        'node_memory_MemFree_bytes / 1024 / 1024',
        "Arithmetic operation",
        [
            ('remove_arithmetic_op', [], {}),
            ('with_arithmetic_op', ['/', 1073741824], {})  # Convert to GB
        ]
    )
    
    # Test 5: Complex query with binary operator
    test_query_preservation(
        '(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100 > 5',
        "Complex query with binary operator",
        [
            ('with_label', ['method', 'GET'], {}),
            ('with_binary_op', ['>', 1], {})  # Change threshold
        ]
    )
    
    # Test 6: Query with rate and offset
    test_query_preservation(
        'rate(http_requests_total[5m] offset 1h)',
        "Query with rate and offset",
        [
            ('with_offset', ['30m'], {}),  # Change offset
            ('with_range', ['1h'], {})     # Change range
        ]
    )

if __name__ == "__main__":
    run_tests() 