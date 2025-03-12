from dataclasses import dataclass, field
from typing import List, Optional, Union, Tuple
from enum import Enum, auto
import re

# Token types for lexical analysis
class TokenType(Enum):
    METRIC_NAME = auto()
    LABEL_NAME = auto()
    LABEL_VALUE = auto()
    LABEL_OP = auto()
    NUMBER = auto()
    DURATION = auto()
    FUNCTION = auto()
    GROUPING = auto()  # 'by' or 'without'
    ARITHMETIC_OP = auto()
    BINARY_OP = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    COMMA = auto()
    OFFSET = auto()
    WHITESPACE = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    position: int

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def read_identifier(self) -> Token:
        result = []
        start_pos = self.pos

        while self.current_char and (self.current_char.isalnum() or self.current_char in '_:'):
            result.append(self.current_char)
            self.advance()

        value = ''.join(result)
        
        # Determine token type
        if value in ('by', 'without'):
            return Token(TokenType.GROUPING, value, start_pos)
        elif value == 'offset':
            return Token(TokenType.OFFSET, value, start_pos)
        elif self.peek_ahead() == '(':
            return Token(TokenType.FUNCTION, value, start_pos)
        else:
            return Token(TokenType.METRIC_NAME, value, start_pos)

    def read_string(self) -> str:
        result = []
        self.advance()  # Skip opening quote
        while self.current_char and self.current_char != '"':
            result.append(self.current_char)
            self.advance()
        self.advance()  # Skip closing quote
        return ''.join(result)

    def peek_ahead(self) -> Optional[str]:
        peek_pos = self.pos + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def tokenize(self) -> List[Token]:
        tokens = []
        
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char.isdigit():
                tokens.append(self.read_number())
                continue
            
            if self.current_char.isalpha() or self.current_char == '_':
                tokens.append(self.read_identifier())
                continue
            
            if self.current_char == '"':
                tokens.append(self.read_string())
                continue
            
            # Handle operators
            if self.current_char in '+-*/%^':
                tokens.append(Token(TokenType.ARITHMETIC_OP, self.current_char, self.pos))
            elif self.current_char in '<>=!':
                tokens.append(self.read_comparison_operator())
            elif self.current_char == '{':
                tokens.append(Token(TokenType.LEFT_BRACE, '{', self.pos))
            elif self.current_char == '}':
                tokens.append(Token(TokenType.RIGHT_BRACE, '}', self.pos))
            elif self.current_char == '[':
                tokens.append(Token(TokenType.LEFT_BRACKET, '[', self.pos))
            elif self.current_char == ']':
                tokens.append(Token(TokenType.RIGHT_BRACKET, ']', self.pos))
            elif self.current_char == '(':
                tokens.append(Token(TokenType.LEFT_PAREN, '(', self.pos))
            elif self.current_char == ')':
                tokens.append(Token(TokenType.RIGHT_PAREN, ')', self.pos))
            elif self.current_char == ',':
                tokens.append(Token(TokenType.COMMA, ',', self.pos))
            
            self.advance()
        
        return tokens

    def read_number(self) -> Token:
        """Read a number token."""
        result = []
        start_pos = self.pos
        
        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            result.append(self.current_char)
            self.advance()
        
        return Token(TokenType.NUMBER, ''.join(result), start_pos)

    def read_comparison_operator(self) -> Token:
        """Read a comparison operator token."""
        result = []
        start_pos = self.pos
        
        while self.current_char and self.current_char in '<>=!':
            result.append(self.current_char)
            self.advance()
        
        return Token(TokenType.BINARY_OP, ''.join(result), start_pos)

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
            labels_str = ",".join(str(label) for label in self.labels)
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

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current_pos = 0

    def current_token(self) -> Optional[Token]:
        if self.current_pos < len(self.tokens):
            return self.tokens[self.current_pos]
        return None

    def advance(self):
        self.current_pos += 1

    def expect(self, token_type: TokenType) -> Token:
        current = self.current_token()
        if current and current.type == token_type:
            self.advance()
            return current
        raise ValueError(f"Expected {token_type}, got {current.type if current else 'EOF'}")

    def match(self, token_type: TokenType) -> bool:
        current = self.current_token()
        if current and current.type == token_type:
            self.advance()
            return True
        return False

    def parse_labels(self) -> List[LabelMatcher]:
        labels = []
        while True:
            name = self.expect(TokenType.LABEL_NAME).value
            op = self.expect(TokenType.LABEL_OP).value
            value = self.expect(TokenType.LABEL_VALUE).value
            labels.append(LabelMatcher(name, value, op))
            
            if not self.match(TokenType.COMMA):
                break
        return labels

    def parse_duration(self) -> str:
        duration = self.expect(TokenType.DURATION).value
        if not re.match(r'^\d+[smhdwy]$', duration):
            raise ValueError(f"Invalid duration format: {duration}")
        return duration

    def parse_metric(self) -> MetricSelector:
        """Parse a metric selector with labels, range, and offset."""
        name = self.expect(TokenType.METRIC_NAME).value
        metric = MetricSelector(name)
        
        # Parse labels if present
        if self.match(TokenType.LEFT_BRACE):
            metric.labels = self.parse_labels()
            self.expect(TokenType.RIGHT_BRACE)
        
        # Parse range window if present
        if self.match(TokenType.LEFT_BRACKET):
            metric.range_window = self.parse_duration()
            self.expect(TokenType.RIGHT_BRACKET)
        
        # Parse offset if present
        if self.match(TokenType.OFFSET):
            metric.offset = self.parse_duration()
        
        return metric

    def parse_function_args(self) -> List[Union[str, MetricSelector, Function]]:
        """Parse function arguments."""
        args = []
        while True:
            if self.current_token().type == TokenType.NUMBER:
                args.append(float(self.current_token().value))
                self.advance()
            else:
                arg = self.parse_term()
                args.append(arg)
            
            if not self.match(TokenType.COMMA):
                break
        return args

    def parse_function(self) -> Function:
        """Parse a function call with its arguments and grouping."""
        name = self.expect(TokenType.FUNCTION).value
        self.expect(TokenType.LEFT_PAREN)
        args = self.parse_function_args()
        self.expect(TokenType.RIGHT_PAREN)
        
        # Parse grouping if present
        by_labels = []
        without_labels = []
        
        if self.match(TokenType.GROUPING):
            grouping_type = self.current_token().value
            self.expect(TokenType.LEFT_PAREN)
            labels = self.parse_label_list()
            self.expect(TokenType.RIGHT_PAREN)
            
            if grouping_type == "by":
                by_labels = labels
            else:
                without_labels = labels
        
        return Function(name, args, by_labels, without_labels)

    def parse_label_list(self) -> List[str]:
        labels = []
        while True:
            labels.append(self.expect(TokenType.LABEL_NAME).value)
            if not self.match(TokenType.COMMA):
                break
        return labels

    def parse_expression(self):
        """Parse a complete PromQL expression."""
        # Handle binary operations
        expr = self.parse_term()
        
        while self.current_token() and self.current_token().type == TokenType.BINARY_OP:
            op = self.current_token().value
            self.advance()
            value = self.expect(TokenType.NUMBER).value
            return expr, op, float(value)
        
        return expr, None, None

    def parse_term(self):
        """Parse a term (metric selector, function call, or parenthesized expression)."""
        if self.match(TokenType.LEFT_PAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RIGHT_PAREN)
            
            # Check for arithmetic operations
            if self.current_token() and self.current_token().type == TokenType.ARITHMETIC_OP:
                op = self.current_token().value
                self.advance()
                value = self.expect(TokenType.NUMBER).value
                return expr, op, float(value)
            
            return expr
        
        if self.current_token() and self.current_token().type == TokenType.FUNCTION:
            return self.parse_function()
        
        return self.parse_metric()

class PromQLBuilder:
    def __init__(self, query: Optional[str] = None):
        self.metric: Optional[MetricSelector] = None
        self.functions: List[Function] = []
        self.binary_ops: List[tuple[str, Union[str, float]]] = []
        self.arithmetic_ops: List[ArithmeticOperation] = []
        
        if query:
            self._parse_query(query)

    def _parse_query(self, query: str) -> None:
        """Parse an existing PromQL query and populate the builder's state."""
        # Clean up input query
        query = query.strip()
        
        # Create lexer and parser
        lexer = Lexer(query)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        
        # Add parse_expression method to Parser class to handle the full query
        def parse_expression(self):
            """Parse a complete PromQL expression."""
            # Handle binary operations
            expr = self.parse_term()
            
            while self.current_token() and self.current_token().type == TokenType.BINARY_OP:
                op = self.current_token().value
                self.advance()
                value = self.expect(TokenType.NUMBER).value
                return expr, op, float(value)
            
            return expr, None, None

        def parse_term(self):
            """Parse a term (metric selector, function call, or parenthesized expression)."""
            if self.match(TokenType.LEFT_PAREN):
                expr = self.parse_expression()
                self.expect(TokenType.RIGHT_PAREN)
                
                # Check for arithmetic operations
                if self.current_token() and self.current_token().type == TokenType.ARITHMETIC_OP:
                    op = self.current_token().value
                    self.advance()
                    value = self.expect(TokenType.NUMBER).value
                    return expr, op, float(value)
                
                return expr
            
            if self.current_token() and self.current_token().type == TokenType.FUNCTION:
                return self.parse_function()
            
            return self.parse_metric()

        Parser.parse_expression = parse_expression
        Parser.parse_term = parse_term

        # Parse the complete query
        try:
            result = parser.parse_expression()
            
            # Handle different types of results
            if isinstance(result, tuple):
                expr, op, value = result
                if op in ["+", "-", "*", "/", "%", "^"]:
                    self.arithmetic_ops.append(ArithmeticOperation(op, value))
                elif op:  # Binary operation
                    self.binary_ops.append((op, value))
                
                if isinstance(expr, MetricSelector):
                    self.metric = expr
                elif isinstance(expr, Function):
                    self.functions.append(expr)
                    if expr.name == "rate" and expr.args:
                        # Extract metric from rate function
                        metric_arg = expr.args[0]
                        if isinstance(metric_arg, MetricSelector):
                            self.metric = metric_arg
            elif isinstance(result, MetricSelector):
                self.metric = result
            elif isinstance(result, Function):
                self.functions.append(result)
                # Handle special case for rate function
                if result.name == "rate" and result.args:
                    metric_arg = result.args[0]
                    if isinstance(metric_arg, MetricSelector):
                        self.metric = metric_arg

        except Exception as e:
            raise ValueError(f"Failed to parse query: {str(e)}")

        # If we couldn't parse a metric, raise an error
        if not self.metric:
            raise ValueError("Could not parse metric from query")

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
        return self.with_function("rate", "$expr")

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

queries = [
    'sum by (job) (rate(http_requests_total{status="500"}[5m]))',
    'histogram_quantile(0.95, sum(rate(http_duration_seconds_bucket[5m])) by (le))',
    '(sum(rate(errors[5m])) / sum(rate(requests[5m]))) * 100',
] 