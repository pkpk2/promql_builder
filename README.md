# PromQL Builder

A Python library that provides a builder pattern implementation for constructing PromQL (Prometheus Query Language) queries programmatically.

## Features

- Fluent interface for building PromQL queries
- Support for metric selectors with labels (including regex matching)
- Support for range windows and offsets
- Support for PromQL functions (rate, sum, etc.) with full grouping clauses
- Support for binary operations and comparisons
- Support for arithmetic operations with both scalars and expressions
- Robust parsing and modification of existing complex PromQL queries
- Advanced lexical analysis and parsing for reliable query manipulation
- Type hints for better IDE support

## Installation

### Using Poetry (Recommended)

```bash
poetry add promql-builder
```

### Using pip

```bash
pip install promql-builder
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/pkpk1/promql_builder.git
cd promql_builder
```

2. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install
```

4. Activate the virtual environment:
```bash
poetry shell
```

## Usage

### Basic Usage

```python
from promql_builder import PromQLBuilder

# Create a simple query
query = (PromQLBuilder()
    .with_metric("http_requests_total")
    .with_label("status", "200")
    .with_label("method", "GET")
    .build())

print(query)  # Output: http_requests_total{status="200",method="GET"}
```

### Using Rate Function

```python
query = (PromQLBuilder()
    .with_metric("http_requests_total")
    .with_label("status", "200")
    .with_rate("5m")
    .build())

print(query)  # Output: rate(http_requests_total{status="200"}[5m])
```

### Complex Queries

```python
query = (PromQLBuilder()
    .with_metric("http_requests_total")
    .with_label("status", "500")
    .with_rate("5m")
    .with_function("sum", "$expr", by=["method"])
    .with_binary_op(">", 10)
    .build())

print(query)  # Output: (sum(rate(http_requests_total{status="500"}[5m])) by (method) > 10)
```

### Parsing and Modifying Existing Queries

```python
existing_query = 'rate(http_requests_total{status="200",method="GET"}[5m])'
builder = PromQLBuilder(existing_query)

# Modify the query
modified_query = (builder
    .with_label("path", "/api", "=~")
    .with_range("10m")
    .build())

print(modified_query)  # Output: rate(http_requests_total{status="200",method="GET",path=~"/api"}[10m])
```

### Complex Query Modifications

```python
# Parse and modify a complex aggregation query
existing_query = 'sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))'
builder = PromQLBuilder(existing_query)

# Add additional conditions 
modified_query = (builder
    .with_label("method", "GET")
    .with_binary_op(">", 100)
    .build())

print(modified_query)
# Output: (sum by (job) (rate(http_requests_total{status=~"5..",method="GET"}[5m])) > 100)
```

### Arithmetic Operations

```python
# Basic arithmetic operations with scalar values
query = (PromQLBuilder()
    .with_metric("http_requests_total")
    .with_label("status", "200")
    .with_rate("5m")
    .with_arithmetic_op("*", 2)  # Multiply by 2
    .with_arithmetic_op("+", 100)  # Add 100
    .build())

print(query)  # Output: ((rate(http_requests_total{status="200"}[5m]) * 2) + 100)
```

### Advanced Histogram Functions

```python
# Histogram quantile with grouping
query = (PromQLBuilder()
    .with_metric("http_request_duration_seconds_bucket")
    .with_label("path", "/api/.*", "=~")
    .with_rate("5m")
    .with_function("histogram_quantile", 0.95, "$expr", by=["path", "method"])
    .build())

print(query)  # Output: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{path=~"/api/.*"}[5m])) by (path, method)
```

## API Reference

### PromQLBuilder

Main class for building PromQL queries.

#### Methods

- `with_metric(name: str) -> PromQLBuilder`: Set the metric name
- `with_label(name: str, value: str, operator: str = "=") -> PromQLBuilder`: Add a label matcher
- `with_range(window: str) -> PromQLBuilder`: Add a range window
- `with_offset(offset: str) -> PromQLBuilder`: Add an offset
- `with_function(name: str, *args, by: Optional[List[str]] = None, without: Optional[List[str]] = None) -> PromQLBuilder`: Add a function call
- `with_rate(window: str = "5m") -> PromQLBuilder`: Add rate() function
- `with_binary_op(operator: str, value: Union[str, float]) -> PromQLBuilder`: Add a binary operation
- `with_arithmetic_op(operator: str, value: Union[str, float, MetricSelector, Function]) -> PromQLBuilder`: Add an arithmetic operation
- `remove_label(name: str) -> PromQLBuilder`: Remove a label matcher
- `remove_function(name: str) -> PromQLBuilder`: Remove a function by name
- `remove_binary_op() -> PromQLBuilder`: Remove the last binary operation
- `remove_arithmetic_op() -> PromQLBuilder`: Remove the last arithmetic operation
- `remove_range() -> PromQLBuilder`: Remove the range window
- `remove_offset() -> PromQLBuilder`: Remove the offset
- `build() -> str`: Build the final PromQL query string

## Examples

For more examples, see the `examples.py` file in the repository. It includes:

- Basic metric selection and rate queries
- Complex aggregations with multiple labels
- Histogram quantiles and percentiles
- Multi-stage operations and arithmetic
- Time shifts and range windows
- Complex query modifications

## License

This project is licensed under the MIT License - see the LICENSE file for details.
