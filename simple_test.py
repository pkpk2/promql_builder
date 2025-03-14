from promql_builder import PromQLBuilder

def test_simple_query():
    """Test that a simple query preserves parameters when modified."""
    query = 'http_requests_total{status="200"}'
    print(f"Original query: {query}")
    
    builder = PromQLBuilder(query)
    print(f"Initial build: {builder.build()}")
    
    # Make modifications
    builder.with_label("method", "GET")
    builder.with_label("environment", "production")
    
    # Check if the modifications are reflected
    modified = builder.build()
    print(f"Modified query: {modified}")
    
    if "method=\"GET\"" in modified and "environment=\"production\"" in modified:
        print("✅ Simple query test passed: Labels were preserved")
    else:
        print("❌ Simple query test failed: Labels were not preserved")

def test_complex_query():
    """Test that a complex query preserves parameters when modified."""
    query = 'sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)'
    print(f"\nOriginal query: {query}")
    
    builder = PromQLBuilder(query)
    print(f"Initial build: {builder.build()}")
    
    # Make modifications
    builder.with_range("10m")
    builder.with_binary_op(">", 100)
    
    # Check if the modifications are reflected
    modified = builder.build()
    print(f"Modified query: {modified}")
    
    if "[10m]" in modified and "> 100" in modified:
        print("✅ Complex query test passed: Range and binary op were preserved")
    else:
        print("❌ Complex query test failed: Range and/or binary op were not preserved")

def test_rate_query():
    """Test that a rate query preserves parameters when modified."""
    query = 'rate(http_requests_total{status="500"}[5m])'
    print(f"\nOriginal query: {query}")
    
    builder = PromQLBuilder(query)
    print(f"Initial build: {builder.build()}")
    
    # Make modifications
    builder.with_range("10m")
    builder.with_offset("1h")
    
    # Check if the modifications are reflected
    modified = builder.build()
    print(f"Modified query: {modified}")
    
    if "[10m]" in modified and "offset 1h" in modified:
        print("✅ Rate query test passed: Range and offset were preserved")
    else:
        print("❌ Rate query test failed: Range and/or offset were not preserved")

if __name__ == "__main__":
    print("Testing PromQLBuilder parameter preservation")
    print("============================================")
    test_simple_query()
    test_complex_query()
    test_rate_query() 