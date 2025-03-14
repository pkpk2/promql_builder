#!/usr/bin/env python3
"""Debug script to investigate PromQLBuilder issues."""

from promql_builder import PromQLBuilder

def debug_query(query):
    """Debug how a query is parsed and rebuilt."""
    print(f"\n--- Debugging query: {query} ---")
    
    # Parse query
    builder = PromQLBuilder(query)
    
    # Print metric info
    print("\nParsed metric:")
    print(f"  Name: {builder.metric.name}")
    print(f"  Labels: {[(l.name, l.operator, l.value) for l in builder.metric.labels]}")
    print(f"  Range window: {builder.metric.range_window}")
    print(f"  Offset: {builder.metric.offset}")
    
    # Print functions
    print("\nParsed functions:")
    for func in builder.functions:
        print(f"  {func.name}({', '.join(str(a) for a in func.args)})")
        if func.group_by:
            print(f"    Group by: {func.group_by}")
        if func.without:
            print(f"    Without: {func.without}")
    
    # Print operations
    print("\nParsed binary operations:")
    for op in builder.binary_ops:
        print(f"  {op.operator} {op.right}")
    
    print("\nParsed arithmetic operations:")
    for op in builder.arithmetic_ops:
        print(f"  {op.operator} {op.value}")
    
    # Rebuild and compare
    rebuilt = builder.build()
    print(f"\nRebuilt query: {rebuilt}")
    print(f"Original query: {query}")
    
    # Check if identical
    identical = rebuilt == query
    print(f"Identical: {'Yes' if identical else 'No'}")

# Debug various query types
debug_query("http_requests_total{status=\"200\"}")
debug_query("rate(http_requests_total{status=\"500\"}[5m])")
debug_query("sum(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) by (job)")
debug_query("sum by (job) (rate(http_requests_total[5m]))")
debug_query("http_requests_total{status=\"200\",method=\"GET\"}") 