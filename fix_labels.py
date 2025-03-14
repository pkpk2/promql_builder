#!/usr/bin/env python3
"""Testing the fixed label regex pattern."""

import re

def test_label_pattern():
    label_patterns = [
        r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([=!]=~?|=~|!~)\s*"([^"]*)"',  # Original pattern
        r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([=!]=~?|=~|!~|=)\s*"([^"]*)"'  # Fixed pattern
    ]
    
    test_strings = [
        'status="200"',
        'method="GET"',
        'status="200",method="GET"',
        'mode!="idle"'
    ]
    
    for i, pattern in enumerate(label_patterns):
        print(f"\nPattern {i+1}: {pattern}")
        for test_str in test_strings:
            matches = re.findall(pattern, test_str)
            print(f"  '{test_str}' -> {matches}")

if __name__ == "__main__":
    test_label_pattern() 