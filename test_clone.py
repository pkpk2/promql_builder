#!/usr/bin/env python3
"""Test the clone method of PromQLBuilder."""

from promql_builder import PromQLBuilder

def test_clone():
    """Test cloning a builder and verifying independence."""
    # Create a query with some complexity
    original_query = "sum(rate(istio_requests_total{cloud_region='eastus2', service_namespace='adm', service_name='adm-store'}[5m])) by (response_code)"
    
    # Parse it into a builder
    original_builder = PromQLBuilder(original_query)
    print(f"Original query: {original_query}")
    print(f"Original builder query: {original_builder.build()}")
    
    # Clone the builder
    cloned_builder = original_builder.clone()
    print(f"Cloned builder (before changes): {cloned_builder.build()}")
    
    # Modify the original builder
    original_builder.with_label("environment", "production")
    original_builder.with_range("10m")
    print(f"Original builder (after changes): {original_builder.build()}")
    
    # Verify cloned builder remained unchanged
    print(f"Cloned builder (should be unchanged): {cloned_builder.build()}")
    
    # Modify the cloned builder differently
    cloned_builder.with_label("datacenter", "west")
    cloned_builder.with_binary_op(">", 100)
    print(f"Cloned builder (after its own changes): {cloned_builder.build()}")
    
    # Final verification that original wasn't affected by clone's changes
    print(f"Original builder (final state): {original_builder.build()}")

if __name__ == "__main__":
    test_clone() 