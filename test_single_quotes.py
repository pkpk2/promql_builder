#!/usr/bin/env python3
"""Test how PromQLBuilder handles single quotes in label values."""

from promql_builder import PromQLBuilder

# Test query with single quotes in label values
query = "sum(rate(istio_requests_total{cloud_region='eastus2', service_namespace='adm', service_name='adm-store'}[5m])) by (response_code)"

print(f"Original query: {query}")

# Try to parse and rebuild
try:
    builder = PromQLBuilder(query)
    
    # Print metric info
    print("\nParsed metric info:")
    print(f"  Name: {builder.metric.name if builder.metric else 'None'}")
    print(f"  Labels: {[(l.name, l.operator, l.value) for l in builder.metric.labels] if builder.metric else []}")
    print(f"  Range window: {builder.metric.range_window if builder.metric else 'None'}")
    
    # Print functions
    print("\nParsed functions:")
    for func in builder.functions:
        print(f"  {func.name}({', '.join(str(a) for a in func.args)})")
        if func.group_by:
            print(f"    Group by: {func.group_by}")
        if func.without:
            print(f"    Without: {func.without}")
    
    # Rebuild
    rebuilt = builder.build()
    print(f"\nRebuilt query: {rebuilt}")
    
    # Test modifications
    builder.with_label("additional_label", "test_value")
    modified = builder.build()
    print(f"\nModified query: {modified}")
    
except Exception as e:
    print(f"\nError: {str(e)}") 