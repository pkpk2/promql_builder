from typing import List, Dict, Optional, Union
import re
from dataclasses import dataclass, field
from typing import Tuple

@dataclass
class LabelMatcher:
    name: str
    value: str
    operator: str = "="

    def __str__(self) -> str:
        return f'{self.name}{self.operator}"{self.value}"'

@dataclass
class MetricSelector:
    name: str
    labels: List[LabelMatcher] = field(default_factory=list)
    range_window: Optional[str] = None
    offset: Optional[str] = None

    def __str__(self) -> str:
        parts = [self.name]
        if self.labels:
            labels_str = ", ".join(str(label) for label in self.labels)
            parts.append(f"{{{labels_str}}}")
        if self.range_window:
            parts.append(f"[{self.range_window}]")
        if self.offset:
            parts.append(f" offset {self.offset}")
        return "".join(parts)

@dataclass
class Function:
    name: str
    args: List[Union[str, 'MetricSelector', 'Function']] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    without: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        result = f"{self.name}({args_str})"
        if self.group_by:
            result += f" by ({', '.join(self.group_by)})"
        elif self.without:
            result += f" without ({', '.join(self.without)})"
        return result

@dataclass
class ArithmeticOperation:
    operator: str
    value: Union[str, float, 'MetricSelector', 'Function']
    is_scalar: bool = True

    def __str__(self) -> str:
        if self.is_scalar:
            return f"{self.operator} {self.value}"
        return f"{self.operator} {str(self.value)}"

class QueryParser:
    @staticmethod
    def parse_label_matchers(label_str: str) -> List[LabelMatcher]:
        """Parse label matchers from a string like '{label1="value1",label2=~"value2"}'"""
        if not label_str or label_str == "{}":
            return []
        
        matchers = []
        # Remove outer braces
        label_str = label_str.strip("{}").strip()
        
        # Split by comma, but not within quotes
        parts = re.findall(r'([^,]+)(?:,|$)', label_str)
        
        for part in parts:
            # Match label name, operator, and value
            match = re.match(r'(\w+)(=~|!~|=|!=)"([^"]*)"', part.strip())
            if match:
                name, op, value = match.groups()
                matchers.append(LabelMatcher(name, value, op))
        
        return matchers

    @staticmethod
    def parse_function(func_str: str) -> Tuple[str, List[str], List[str], List[str]]:
        """Parse function and its grouping."""
        # Match function name, arguments, and by/without clauses with improved regex
        func_match = re.match(
            r'(?P<func>\w+)\s*\(\s*(?P<args>.*?)\s*\)'
            r'(?:\s+(?P<grouping>by|without)\s+\((?P<labels>[^)]*)\))?',
            func_str,
            re.DOTALL
        )
        
        if not func_match:
            return None, [], [], []
        
        match_dict = func_match.groupdict()
        name = match_dict['func']
        args = [arg.strip() for arg in match_dict['args'].split(",")] if match_dict['args'] else []
        
        # Handle by/without clauses
        group_type = match_dict['grouping']
        group_labels = []
        if group_type and match_dict['labels']:
            group_labels = [l.strip() for l in match_dict['labels'].split(",")]
        
        # Return appropriate lists for by and without
        by_labels = group_labels if group_type == "by" else []
        without_labels = group_labels if group_type == "without" else []
        
        return name, args, by_labels, without_labels

    @staticmethod
    def parse_range_and_offset(metric_str: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse range window and offset from metric string."""
        range_match = re.search(r'\[(\d+[smhdwy])\]', metric_str)
        offset_match = re.search(r'offset\s+(\d+[smhdwy])', metric_str)
        
        range_window = range_match.group(1) if range_match else None
        offset = offset_match.group(1) if offset_match else None
        
        return range_window, offset

    @staticmethod
    def parse_arithmetic_operation(expr: str) -> Tuple[Optional[str], Optional[Union[str, float]]]:
        """Parse arithmetic operation from expression."""
        # Match arithmetic operators and their operands
        op_match = re.match(r'\((.*?)\)\s*([+\-*/%^])\s*(\d+(?:\.\d+)?)', expr)
        if not op_match:
            return None, None
        
        return op_match.group(2), float(op_match.group(3))

class PromQLBuilder:
    def __init__(self, query: Optional[str] = None):
        self.metric: Optional[MetricSelector] = None
        self.functions: List[Function] = []
        self.binary_ops: List[tuple[str, Union[str, float]]] = []
        self.arithmetic_ops: List[ArithmeticOperation] = []
        
        if query:
            self._parse_query(query)

    def _parse_query(self, query: str) -> None:
        """Parse an existing PromQL query."""
        # Handle binary operations first
        binary_op_match = re.match(r'\((.*?)\)\s*([<>=!]+|and|or|unless)\s*(\d+(?:\.\d+)?)', query)
        if binary_op_match:
            query = binary_op_match.group(1)
            self.binary_ops.append((binary_op_match.group(2), float(binary_op_match.group(3))))

        # Handle arithmetic operations
        while True:
            op, value = QueryParser.parse_arithmetic_operation(query)
            if not op:
                break
            self.arithmetic_ops.append(ArithmeticOperation(op, value))
            query = query[query.find("(")+1:query.find(")")]

        # Handle functions and aggregations
        while True:
            # Match function with potential by/without clause
            # Updated regex to better handle aggregation operators and their clauses
            func_match = re.match(
                r'(?P<func>\w+)\s*\(\s*(?P<content>.*?)\s*\)'
                r'(?:\s+(?P<grouping>by|without)\s+\((?P<labels>[^)]*)\))?',
                query,
                re.DOTALL
            )
            
            if not func_match:
                break
            
            func_dict = func_match.groupdict()
            func_name = func_dict['func']
            func_content = func_dict['content']
            grouping_type = func_dict['grouping']
            grouping_labels = func_dict['labels']

            # Process grouping labels
            by_labels = []
            without_labels = []
            if grouping_labels:
                labels = [l.strip() for l in grouping_labels.split(',')]
                if grouping_type == 'by':
                    by_labels = labels
                else:
                    without_labels = labels

            # For rate function, extract range window from the inner content
            if func_name == "rate":
                range_match = re.search(r'\[(\d+[smhdwy])\]', func_content)
                if range_match:
                    if not self.metric:
                        self.metric = MetricSelector("")
                    self.metric.range_window = range_match.group(1)

            # Create function with proper grouping
            func = Function(func_name, ["$expr"], by_labels, without_labels)
            self.functions.insert(0, func)

            # Update query to process next function
            query = func_content

        # Parse metric and labels
        # Updated regex to better handle metric names and label matchers
        metric_match = re.match(
            r'(?P<metric>[a-zA-Z_:][a-zA-Z0-9_:]*)'  # metric name
            r'(?:\{(?P<labels>.*?)\})?'  # optional labels
            r'(?:\[(?P<range>[^]]+)\])?'  # optional range
            r'(?:\s+offset\s+(?P<offset>\w+))?$',  # optional offset
            query
        )

        if metric_match:
            match_dict = metric_match.groupdict()
            metric_name = match_dict['metric']
            label_str = match_dict['labels'] or ""
            range_str = match_dict['range']
            offset_str = match_dict['offset']

            self.metric = MetricSelector(metric_name)
            if label_str:
                self.metric.labels = QueryParser.parse_label_matchers(f"{{{label_str}}}")
            if range_str:
                self.metric.range_window = range_str
            if offset_str:
                self.metric.offset = offset_str

    @staticmethod
    def parse_duration(duration: str) -> str:
        """Validate and normalize duration string."""
        if not re.match(r'^\d+[smhdwy]$', duration):
            raise ValueError(f"Invalid duration format: {duration}")
        return duration

    def with_metric(self, name: str) -> 'PromQLBuilder':
        """Set the metric name."""
        self.metric = MetricSelector(name)
        return self

    def with_label(self, name: str, value: str, operator: str = "=") -> 'PromQLBuilder':
        """Add a label matcher."""
        if not self.metric:
            raise ValueError("No metric selected")
        if operator not in ["=", "!=", "=~", "!~"]:
            raise ValueError(f"Invalid operator: {operator}")
        
        # Remove existing label with same name if it exists
        self.remove_label(name)
        
        self.metric.labels.append(LabelMatcher(name, value, operator))
        return self

    def with_range(self, window: str) -> 'PromQLBuilder':
        """Add a range window."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.range_window = self.parse_duration(window)
        return self

    def with_offset(self, offset: str) -> 'PromQLBuilder':
        """Add an offset."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.offset = self.parse_duration(offset)
        return self

    def with_function(self, name: str, *args: Union[str, MetricSelector, Function], 
                     by: Optional[List[str]] = None, 
                     without: Optional[List[str]] = None) -> 'PromQLBuilder':
        """Add a function call."""
        func = Function(name, list(args), by or [], without or [])
        self.functions.append(func)
        return self

    def with_rate(self, window: str = "5m") -> 'PromQLBuilder':
        """Add rate() function."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.range_window = self.parse_duration(window)
        return self.with_function("rate", self.metric)

    def with_binary_op(self, operator: str, value: Union[str, float]) -> 'PromQLBuilder':
        """Add a binary operation."""
        valid_ops = ["+", "-", "*", "/", "%", "^", "==", "!=", ">", "<", ">=", "<=", "and", "or", "unless"]
        if operator not in valid_ops:
            raise ValueError(f"Invalid operator: {operator}")
        self.binary_ops.append((operator, value))
        return self

    def with_arithmetic_op(self, operator: str, value: Union[str, float, MetricSelector, Function]) -> 'PromQLBuilder':
        """Add an arithmetic operation."""
        valid_ops = ["+", "-", "*", "/", "%", "^"]
        if operator not in valid_ops:
            raise ValueError(f"Invalid operator: {operator}")
        
        is_scalar = isinstance(value, (str, float)) or (isinstance(value, str) and value.replace('.', '').isdigit())
        self.arithmetic_ops.append(ArithmeticOperation(operator, value, is_scalar))
        return self

    def remove_label(self, name: str) -> 'PromQLBuilder':
        """Remove a label matcher."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.labels = [l for l in self.metric.labels if l.name != name]
        return self

    def remove_function(self, name: str) -> 'PromQLBuilder':
        """Remove a function by name."""
        self.functions = [f for f in self.functions if f.name != name]
        return self

    def remove_binary_op(self) -> 'PromQLBuilder':
        """Remove the last binary operation."""
        if self.binary_ops:
            self.binary_ops.pop()
        return self

    def remove_arithmetic_op(self) -> 'PromQLBuilder':
        """Remove the last arithmetic operation."""
        if self.arithmetic_ops:
            self.arithmetic_ops.pop()
        return self

    def remove_range(self) -> 'PromQLBuilder':
        """Remove the range window."""
        if self.metric:
            self.metric.range_window = None
        return self

    def remove_offset(self) -> 'PromQLBuilder':
        """Remove the offset."""
        if self.metric:
            self.metric.offset = None
        return self

    def build(self) -> str:
        """Build the final PromQL query string."""
        if not self.metric:
            raise ValueError("No metric selected")

        # Start with the metric
        expr = str(self.metric)

        # Apply functions in order
        for func in self.functions:
            if func.name == "rate" and self.metric.range_window:
                # Special handling for rate to use metric's range window
                expr = f"rate({expr})"
            else:
                # Replace any placeholder with the current expression
                args = [str(arg).replace("$expr", expr) for arg in func.args]
                expr = str(Function(func.name, args, func.group_by, func.without))

        # Apply arithmetic operations
        for op in self.arithmetic_ops:
            expr = f"({expr} {op})"

        # Apply binary operations
        for op, value in self.binary_ops:
            expr = f"({expr} {op} {value})"

        return expr

# Example usage
if __name__ == "__main__":
    # Example 1: Parse and modify existing query
    existing_query = 'rate(http_requests_total{status="200",method="GET"}[5m])'
    modifier = PromQLBuilder(existing_query)
    
    print("Existing query:", existing_query)
    print("Modifier:", modifier.build())
    # Add new label and change window
    modified_query = (modifier
                     .with_label("path", "/api", "=~")
                     .with_range("10m")
                     .build())
    print("Modified query:", modified_query)

    print("--------------------------------")

    # Example 2: Parse complex query and modify
    complex_query = 'sum(rate(http_requests_total{status="500"}[5m])) by (method) > 10'
    modifier2 = PromQLBuilder(complex_query)
    
    print("Existing query:", complex_query)
    print("Modifier:", modifier2.build())

    # Remove threshold and add new conditions
    modified_query2 = (modifier2
                      .remove_binary_op()
                      .with_label("path", "/api/.*", "=~")
                      .remove_function("sum")
                      .with_function("sum", "$expr", by=["path", "method"])
                      .build())
    print("\nModified complex query:", modified_query2)

    print("--------------------------------")

    # Example 3: Remove conditions from existing query
    query_with_labels = 'http_requests_total{status="200",method="GET",path="/api"}'
    modifier3 = PromQLBuilder(query_with_labels)
    
    print("Existing query:", query_with_labels)
    print("Modifier:", modifier3.build())

    # Remove some labels
    modified_query3 = (modifier3
                      .remove_label("method")
                      .remove_label("path")
                      .build())
    print("\nQuery after removing labels:", modified_query3)

    print("--------------------------------")

    # Example 4: Arithmetic operations
    query = (PromQLBuilder()
        .with_metric("http_requests_total")
        .with_label("status", "200")
        .with_rate("5m")
        .with_arithmetic_op("*", 2)
        .with_arithmetic_op("+", 100)
        .build())
    print("\nQuery with arithmetic operations:", query)

    print("--------------------------------")
    
    # Example 5: Complex aggregation queries
    complex_queries = [
        'sum(rate(http_requests_total{status="500"}[5m])) by (method)',
        'avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)',
        'sum by (job) (rate(http_requests_total{code=~"5.."}[5m]))',
        'max without (instance) (rate(node_cpu_seconds_total{mode!="idle"}[5m]))',
        'sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (container, pod)',
        'sum by (instance, mode) (rate(node_cpu_seconds_total{mode!="idle"}[5m]))',
        'avg without (instance) (rate(node_memory_MemAvailable_bytes[5m]))',
        'topk(5, sum(rate(http_requests_total[5m])) by (path))'
    ]
    
    print("\nTesting complex query parsing:")
    for query in complex_queries:
        print(f"\nOriginal query: {query}")
        builder = PromQLBuilder(query)
        rebuilt = builder.build()
        print(f"Rebuilt query:  {rebuilt}")
        if query != rebuilt:
            print("WARNING: Queries don't match exactly!") 