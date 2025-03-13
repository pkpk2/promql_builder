from promql_builder import PromQLBuilder
import unittest

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

class TestPromQLBuilderInfoAPI(unittest.TestCase):
    
    def test_get_metric_name(self):
        """Test retrieving the metric name."""
        # Simple metric
        builder = PromQLBuilder("http_requests_total")
        self.assertEqual(builder.get_metric_name(), "http_requests_total")
        
        # Metric within function
        builder = PromQLBuilder("rate(http_requests_total[5m])")
        self.assertEqual(builder.get_metric_name(), "http_requests_total")
        
        # Empty builder
        empty_builder = PromQLBuilder()
        self.assertIsNone(empty_builder.get_metric_name())
    
    def test_get_labels(self):
        """Test retrieving label information."""
        # Directly create a builder with labels instead of parsing
        builder = PromQLBuilder()
        builder.with_metric("http_requests_total")
        builder.with_label("status", "200")
        builder.with_label("method", "GET")
        
        labels = builder.get_labels()
        
        # Verify we got two labels
        self.assertEqual(len(labels), 2)
        
        # Check that the labels have the expected structure
        expected_labels = [
            {'name': 'status', 'value': '200', 'operator': '='},
            {'name': 'method', 'value': 'GET', 'operator': '='}
        ]
        
        # The order might vary, so we'll check that each expected label is in the result
        for expected in expected_labels:
            self.assertIn(expected, labels)
        
        # Test with no labels
        simple_builder = PromQLBuilder()
        simple_builder.with_metric("metric_without_labels")
        self.assertEqual(simple_builder.get_labels(), [])
        
        # Test with different operators
        regex_builder = PromQLBuilder()
        regex_builder.with_metric("api_http_requests_total")
        regex_builder.with_label("path", "/api/v1/.*", "=~")
        
        regex_labels = regex_builder.get_labels()
        self.assertEqual(len(regex_labels), 1)
        self.assertEqual(regex_labels[0]['operator'], '=~')
    
    def test_get_label_values(self):
        """Test retrieving label values as a dictionary."""
        # Directly create a builder with labels instead of parsing
        builder = PromQLBuilder()
        builder.with_metric("http_requests_total")
        builder.with_label("status", "200")
        builder.with_label("method", "GET")
        
        label_values = builder.get_label_values()
        
        expected_values = {
            'status': '200',
            'method': 'GET'
        }
        
        self.assertEqual(label_values, expected_values)
        
        # Empty labels
        empty_builder = PromQLBuilder()
        empty_builder.with_metric("just_a_metric")
        self.assertEqual(empty_builder.get_label_values(), {})
    
    def test_get_functions(self):
        """Test retrieving function information."""
        # Simple function
        builder = PromQLBuilder("rate(http_requests_total[5m])")
        functions = builder.get_functions()
        
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]['name'], 'rate')
        
        # Function with grouping
        builder = PromQLBuilder("sum(rate(http_requests_total[5m])) by (status, method)")
        functions = builder.get_functions()
        
        self.assertEqual(len(functions), 2)  # sum and rate
        
        # Find the sum function (might be in any order)
        sum_func = next((f for f in functions if f['name'] == 'sum'), None)
        self.assertIsNotNone(sum_func)
        self.assertEqual(sum_func['group_by'], ['status', 'method'])
        
        # Without clause
        builder = PromQLBuilder("max(http_requests_total) without (instance)")
        functions = builder.get_functions()
        
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]['name'], 'max')
        self.assertEqual(functions[0]['without'], ['instance'])
    
    def test_get_range_window(self):
        """Test retrieving the range window."""
        # With range window
        builder = PromQLBuilder("http_requests_total[5m]")
        self.assertEqual(builder.get_range_window(), "5m")
        
        # No range window
        builder = PromQLBuilder("http_requests_total")
        self.assertIsNone(builder.get_range_window())
        
        # Range window in function
        builder = PromQLBuilder("rate(http_requests_total[1h])")
        self.assertEqual(builder.get_range_window(), "1h")
    
    def test_get_offset(self):
        """Test retrieving the offset."""
        # With offset
        builder = PromQLBuilder("http_requests_total offset 1d")
        self.assertEqual(builder.get_offset(), "1d")
        
        # No offset
        builder = PromQLBuilder("http_requests_total")
        self.assertIsNone(builder.get_offset())
        
        # Offset with range
        builder = PromQLBuilder("http_requests_total[5m] offset 1h")
        self.assertEqual(builder.get_offset(), "1h")
    
    def test_get_binary_ops(self):
        """Test retrieving binary operations."""
        # With binary operation
        builder = PromQLBuilder("http_requests_total > 100")
        binary_ops = builder.get_binary_ops()
        
        self.assertEqual(len(binary_ops), 1)
        self.assertEqual(binary_ops[0]['operator'], '>')
        self.assertEqual(binary_ops[0]['value'], 100.0)
        
        # Multiple operations
        builder = PromQLBuilder()
        builder.with_metric("http_requests_total")
        builder.with_binary_op(">", 100)
        builder.with_binary_op("or", "up == 1")
        
        binary_ops = builder.get_binary_ops()
        self.assertEqual(len(binary_ops), 2)
        self.assertEqual(binary_ops[0]['operator'], '>')
        self.assertEqual(binary_ops[1]['operator'], 'or')
    
    def test_get_arithmetic_ops(self):
        """Test retrieving arithmetic operations."""
        # With arithmetic operation
        builder = PromQLBuilder("http_requests_total * 100")
        arith_ops = builder.get_arithmetic_ops()
        
        self.assertEqual(len(arith_ops), 1)
        self.assertEqual(arith_ops[0]['operator'], '*')
        self.assertEqual(arith_ops[0]['value'], 100.0)
        self.assertTrue(arith_ops[0]['is_scalar'])
        
        # Multiple operations
        builder = PromQLBuilder()
        builder.with_metric("http_requests_total")
        builder.with_arithmetic_op("*", 100)
        builder.with_arithmetic_op("/", 60)
        
        arith_ops = builder.get_arithmetic_ops()
        self.assertEqual(len(arith_ops), 2)
        self.assertEqual(arith_ops[0]['operator'], '*')
        self.assertEqual(arith_ops[1]['operator'], '/')
    
    def test_get_query_info(self):
        """Test retrieving comprehensive query information."""
        # Directly create a builder with all components instead of parsing
        builder = PromQLBuilder()
        builder.with_metric("http_requests_total")
        builder.with_label("status", "200")
        builder.with_range("5m")
        builder.with_function("rate", "$expr")
        builder.with_function("sum", "$expr", by=["instance"])
        
        info = builder.get_query_info()
        
        # Check all components are present
        self.assertEqual(info['metric_name'], "http_requests_total")
        self.assertEqual(len(info['labels']), 1)
        self.assertEqual(info['labels'][0]['name'], "status")
        self.assertEqual(info['labels'][0]['value'], "200")
        
        self.assertEqual(info['range_window'], "5m")
        self.assertIsNone(info['offset'])
        
        # Should have two functions: rate and sum
        self.assertEqual(len(info['functions']), 2)
        
        # Find the sum function
        sum_func = next((f for f in info['functions'] if f['name'] == 'sum'), None)
        self.assertIsNotNone(sum_func)
        self.assertEqual(sum_func['group_by'], ['instance'])
        
        # Check full query is included
        self.assertIsNotNone(info['full_query'])

    def test_building_and_querying(self):
        """Test building a query and then extracting information from it."""
        # Create a builder and add components
        builder = PromQLBuilder()
        builder.with_metric("node_cpu_seconds_total")
        builder.with_label("mode", "idle")
        builder.with_label("job", "node_exporter")
        builder.with_range("5m")
        builder.with_function("rate", "$expr")
        builder.with_function("sum", "$expr", by=["instance"])
        builder.with_arithmetic_op("*", 100)
        builder.with_binary_op(">", 80)
        
        # Now extract and verify the information
        info = builder.get_query_info()
        
        self.assertEqual(info['metric_name'], "node_cpu_seconds_total")
        
        # Check labels
        labels = info['labels']
        self.assertEqual(len(labels), 2)
        label_dict = {label['name']: label['value'] for label in labels}
        self.assertEqual(label_dict['mode'], "idle")
        self.assertEqual(label_dict['job'], "node_exporter")
        
        # Check functions (order matters here because of how we built it)
        functions = info['functions']
        self.assertEqual(len(functions), 2)
        self.assertEqual(functions[0]['name'], "rate")
        self.assertEqual(functions[1]['name'], "sum")
        self.assertEqual(functions[1]['group_by'], ["instance"])
        
        # Check range window
        self.assertEqual(info['range_window'], "5m")
        
        # Check arithmetic ops
        arith_ops = info['arithmetic_ops']
        self.assertEqual(len(arith_ops), 1)
        self.assertEqual(arith_ops[0]['operator'], "*")
        self.assertEqual(arith_ops[0]['value'], 100)
        
        # Check binary ops
        binary_ops = info['binary_ops']
        self.assertEqual(len(binary_ops), 1)
        self.assertEqual(binary_ops[0]['operator'], ">")
        self.assertEqual(binary_ops[0]['value'], 80)

    def test_deduplication(self):
        """Test that adding the same label or function replaces the existing one."""
        # Test label deduplication
        builder = PromQLBuilder()
        builder.with_metric("http_requests_total")
        builder.with_label("status", "200")
        
        # Add the same label again with a different value
        builder.with_label("status", "500")
        
        # Verify there's still only one label
        labels = builder.get_labels()
        self.assertEqual(len(labels), 1)
        self.assertEqual(labels[0]['name'], "status")
        self.assertEqual(labels[0]['value'], "500")
        
        # Test function deduplication
        builder.with_function("rate", "$expr")
        builder.with_function("sum", "$expr", by=["instance"])
        
        # Now add rate again with different arguments
        builder.with_function("rate", "$expr", by=["method"])
        
        # Verify there are still only two functions
        functions = builder.get_functions()
        self.assertEqual(len(functions), 2)
        
        # Find the rate function
        rate_func = next((f for f in functions if f['name'] == 'rate'), None)
        self.assertIsNotNone(rate_func)
        
        # Verify it has the updated grouping
        self.assertEqual(rate_func['group_by'], ["method"])
        
        # Check full query to make sure everything is there
        query = builder.build()
        self.assertIn("http_requests_total{status=\"500\"}", query)
        self.assertIn("rate(", query)
        self.assertIn("by (method)", query)

# Example usage outside of tests
def example_usage():
    """Show how to use the PromQLBuilder API in a non-test context."""
    # Parse an existing query
    query = 'sum(rate(http_requests_total{status="500", handler=~"/api/.*"}[5m])) by (instance) > 10'
    builder = PromQLBuilder(query)
    
    # Get information about the query
    info = builder.get_query_info()
    
    print("Metric name:", info['metric_name'])
    print("Labels:", info['labels'])
    print("Range window:", info['range_window'])
    
    # Access functions
    for func in info['functions']:
        print(f"Function: {func['name']}")
        if func['group_by']:
            print(f"  Grouped by: {', '.join(func['group_by'])}")
    
    # Check if query has a threshold condition
    binary_ops = info['binary_ops']
    if binary_ops:
        print(f"Alert threshold: {binary_ops[0]['operator']} {binary_ops[0]['value']}")
    
    # Modify the query and get updated information
    builder.with_label("environment", "production")
    builder.with_binary_op(">", 5)  # Lower the threshold
    
    # Get new information after modifications
    new_info = builder.get_query_info()
    print("\nModified query:")
    print("New labels:", new_info['labels'])
    print("New threshold:", new_info['binary_ops'][0]['value'])
    print("Full query:", new_info['full_query'])

if __name__ == '__main__':
    # Run the example if file is executed directly
    example_usage()
    
    # Or run the tests
    unittest.main() 