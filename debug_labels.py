#!/usr/bin/env python3
"""Debug script to fix label parsing in PromQLBuilder."""

from promql_builder import PromQLBuilder
import re

def test_label_parsing():
    """Test the label parsing functionality."""
    queries = [
        "http_requests_total{status=\"200\"}",
        "http_requests_total{status=\"200\",method=\"GET\"}",
        "rate(http_requests_total{status=\"500\"}[5m])",
        "sum(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) by (job)"
    ]
    
    print("Testing label parsing:")
    print("=====================")
    
    for query in queries:
        print(f"\nQuery: {query}")
        
        # Manual label extraction for debugging
        labels_matches = re.findall(r'{([^}]*)}', query)
        print(f"Raw regex matches: {labels_matches}")
        
        for labels_str in labels_matches:
            # This is similar to _parse_labels in PromQLBuilder
            label_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([=!]=~?|=~|!~)\s*"([^"]*)"', labels_str)
            print(f"Parsed labels: {label_matches}")
        
        # Test with regular PromQLBuilder
        builder = PromQLBuilder(query)
        print(f"PromQLBuilder parsed labels: {builder.metric.labels}")
        
if __name__ == "__main__":
    test_label_parsing() 