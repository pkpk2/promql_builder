#!/usr/bin/env python3
"""
PromQL Builder Deduplication Demo

This script demonstrates how the PromQLBuilder properly deduplicates
labels and functions when they are added to a query.
"""

from promql_builder import PromQLBuilder
import json

def demonstrate_deduplication():
    """Demonstrate how deduplication works for labels and functions."""
    print("\n--- Demonstrating Deduplication ---\n")
    
    # Create a basic query
    builder = PromQLBuilder()
    builder.with_metric("http_requests_total")
    builder.with_label("status", "200")
    builder.with_label("method", "GET")
    builder.with_function("rate", "$expr")
    
    # Print the initial query
    initial_query = builder.build()
    initial_info = builder.get_query_info()
    print(f"Initial query: {initial_query}")
    print(f"Initial labels: {json.dumps(initial_info['labels'], indent=2)}")
    print(f"Initial functions: {json.dumps(initial_info['functions'], indent=2)}")
    
    # Now modify the same label and function
    print("\nModifying existing label and function...")
    builder.with_label("status", "500")  # Change status from 200 to 500
    builder.with_function("rate", "$expr", by=["method"])  # Add a 'by' clause to rate
    
    # Print the updated query
    modified_query = builder.build()
    modified_info = builder.get_query_info()
    print(f"Modified query: {modified_query}")
    print(f"Modified labels: {json.dumps(modified_info['labels'], indent=2)}")
    print(f"Modified functions: {json.dumps(modified_info['functions'], indent=2)}")
    
    # Add a new label and function
    print("\nAdding new label and function...")
    builder.with_label("path", "/api", "=~")
    builder.with_function("sum", "$expr", by=["instance"])
    
    # Print the final query
    final_query = builder.build()
    final_info = builder.get_query_info()
    print(f"Final query: {final_query}")
    print(f"Final labels: {json.dumps(final_info['labels'], indent=2)}")
    print(f"Final functions: {json.dumps(final_info['functions'], indent=2)}")
    
    print("\nNote how the 'status' label was updated rather than duplicated,")
    print("and the 'rate' function was updated with a grouping clause.")

if __name__ == "__main__":
    demonstrate_deduplication() 