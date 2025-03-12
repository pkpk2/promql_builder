from dataclasses import dataclass, field
from typing import List, Optional, Union, Tuple
from enum import Enum, auto
import re

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
    STRING = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    position: int

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
    args: List[Union[str, float, 'MetricSelector', 'Function']] = field(default_factory=list)
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
    value: Union[str, float, MetricSelector, Function]
    is_scalar: bool = True

    def __str__(self) -> str:
        if self.is_scalar:
            return f"{self.operator} {self.value}"
        return f"{self.operator} {str(self.value)}"

@dataclass
class BinaryOperation:
    operator: str
    right: Union[float, str, MetricSelector, Function]
    
    def __str__(self) -> str:
        if isinstance(self.right, (float, int)):
            return f"{self.operator} {self.right}"
        return f"{self.operator} {str(self.right)}"

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None

    def error(self):
        raise ValueError(f'Invalid character {self.current_char} at position {self.pos}')

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def peek(self) -> Optional[str]:
        peek_pos = self.pos + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def read_number(self) -> Token:
        result = []
        start_pos = self.pos
        has_dot = False

        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if has_dot:
                    break
                has_dot = True
            result.append(self.current_char)
            self.advance()

        # Check if it's a duration
        if self.current_char and self.current_char in 'smhdwy':
            result.append(self.current_char)
            self.advance()
            return Token(TokenType.DURATION, ''.join(result), start_pos)

        return Token(TokenType.NUMBER, ''.join(result), start_pos)

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
        elif self.current_char == '(':
            return Token(TokenType.FUNCTION, value, start_pos)
        else:
            # Check if it's a label name in a label context
            if self.current_char in ('=', '!', '~'):
                return Token(TokenType.LABEL_NAME, value, start_pos)
            return Token(TokenType.METRIC_NAME, value, start_pos)

    def read_string(self) -> Token:
        result = []
        start_pos = self.pos
        self.advance()  # Skip opening quote

        while self.current_char and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char:
                    result.append(self.current_char)
            else:
                result.append(self.current_char)
            self.advance()

        if self.current_char == '"':
            self.advance()  # Skip closing quote
        
        return Token(TokenType.STRING, ''.join(result), start_pos)

    def read_operator(self) -> Token:
        start_pos = self.pos
        op = self.current_char
        self.advance()

        # Handle two-character operators
        if self.current_char in ('=', '~'):
            op += self.current_char
            self.advance()

        if op in ('=', '!=', '=~', '!~'):
            return Token(TokenType.LABEL_OP, op, start_pos)
        elif op in ('>', '<', '>=', '<=', '==', '!='):
            return Token(TokenType.BINARY_OP, op, start_pos)
        else:
            return Token(TokenType.ARITHMETIC_OP, op, start_pos)

    def tokenize(self) -> List[Token]:
        tokens = []

        while self.current_char is not None:
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

            if self.current_char in ('=', '!', '<', '>', '+', '-', '*', '/', '%', '^'):
                tokens.append(self.read_operator())
                continue

            if self.current_char == '{':
                tokens.append(Token(TokenType.LEFT_BRACE, '{', self.pos))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TokenType.RIGHT_BRACE, '}', self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(TokenType.LEFT_BRACKET, '[', self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TokenType.RIGHT_BRACKET, ']', self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TokenType.LEFT_PAREN, '(', self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TokenType.RIGHT_PAREN, ')', self.pos))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TokenType.COMMA, ',', self.pos))
                self.advance()
            else:
                self.error()

        return tokens

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def peek(self) -> Optional[Token]:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None

    def advance(self):
        self.pos += 1

    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token and token.type == token_type:
            self.advance()
            return token
        raise ValueError(f"Expected {token_type}, got {token.type if token else 'EOF'}")

    def parse_label_matchers(self) -> List[LabelMatcher]:
        matchers = []
        
        while True:
            # Accept either LABEL_NAME or METRIC_NAME (for identifiers in label context)
            if self.current_token().type == TokenType.LABEL_NAME:
                name_token = self.current_token()
                self.advance()
            elif self.current_token().type == TokenType.METRIC_NAME:
                name_token = self.current_token()
                self.advance()
            else:
                raise ValueError(f"Expected label name, got {self.current_token().type}")
                
            op_token = self.expect(TokenType.LABEL_OP)
            value_token = self.expect(TokenType.STRING)
            
            matchers.append(LabelMatcher(name_token.value, value_token.value, op_token.value))
            
            if not self.current_token() or self.current_token().type == TokenType.RIGHT_BRACE:
                break
                
            self.expect(TokenType.COMMA)
        
        return matchers

    def parse_metric(self) -> MetricSelector:
        name = self.expect(TokenType.METRIC_NAME).value
        metric = MetricSelector(name)

        # Parse labels if present
        if self.current_token() and self.current_token().type == TokenType.LEFT_BRACE:
            self.advance()
            metric.labels = self.parse_label_matchers()
            self.expect(TokenType.RIGHT_BRACE)

        # Parse range window if present
        if self.current_token() and self.current_token().type == TokenType.LEFT_BRACKET:
            self.advance()
            metric.range_window = self.expect(TokenType.DURATION).value
            self.expect(TokenType.RIGHT_BRACKET)

        # Parse offset if present
        if self.current_token() and self.current_token().type == TokenType.OFFSET:
            self.advance()
            metric.offset = self.expect(TokenType.DURATION).value

        return metric

    def parse_grouping(self) -> Tuple[List[str], List[str]]:
        """Parse a 'by' or 'without' grouping clause."""
        by_labels = []
        without_labels = []
        
        if not self.current_token() or self.current_token().type != TokenType.GROUPING:
            return by_labels, without_labels
            
        grouping_type = self.current_token().value
        self.advance()
        
        self.expect(TokenType.LEFT_PAREN)
        labels = []
        
        while self.current_token() and self.current_token().type != TokenType.RIGHT_PAREN:
            if self.current_token().type == TokenType.LABEL_NAME:
                labels.append(self.current_token().value)
                self.advance()
            elif self.current_token().type == TokenType.METRIC_NAME:
                # For 'by' and 'without' clauses, we treat metric names as label names
                labels.append(self.current_token().value)
                self.advance()
            else:
                raise ValueError(f"Expected label name, got {self.current_token().type}")
                
            if self.current_token() and self.current_token().type == TokenType.COMMA:
                self.advance()
                continue
            elif self.current_token() and self.current_token().type == TokenType.RIGHT_PAREN:
                break
            else:
                raise ValueError(f"Expected comma or right parenthesis, got {self.current_token().type}")
        
        self.expect(TokenType.RIGHT_PAREN)
        
        if grouping_type == 'by':
            by_labels = labels
        else:
            without_labels = labels
            
        return by_labels, without_labels

    def parse_function_args(self) -> List[Union[str, float, MetricSelector, Function]]:
        """Parse function arguments."""
        args = []
        
        if self.current_token() and self.current_token().type == TokenType.RIGHT_PAREN:
            return args
            
        while True:
            if not self.current_token():
                break

            if self.current_token().type == TokenType.NUMBER:
                args.append(float(self.current_token().value))
                self.advance()
            elif self.current_token().type == TokenType.STRING:
                args.append(self.current_token().value)
                self.advance()
            else:
                # Parse a more complex expression as argument
                args.append(self.parse_expression())

            if not self.current_token() or self.current_token().type == TokenType.RIGHT_PAREN:
                break
                
            if self.current_token().type == TokenType.COMMA:
                self.advance()
            else:
                raise ValueError(f"Expected comma or right parenthesis, got {self.current_token().type}")

        return args

    def parse_function(self) -> Function:
        """Parse a function call with possible grouping."""
        name = self.expect(TokenType.FUNCTION).value
        self.expect(TokenType.LEFT_PAREN)
        args = self.parse_function_args()
        self.expect(TokenType.RIGHT_PAREN)

        # Check for grouping clause (by/without)
        by_labels, without_labels = [], []
        if self.current_token() and self.current_token().type == TokenType.GROUPING:
            by_labels, without_labels = self.parse_grouping()

        return Function(name, args, by_labels, without_labels)

    def parse_binary_op(self, left) -> Union[MetricSelector, Function, BinaryOperation, Tuple]:
        """Parse a binary operation between two expressions."""
        if not self.current_token() or self.current_token().type != TokenType.BINARY_OP:
            return left
            
        op = self.current_token().value
        self.advance()
        
        # Parse the right side of the operation
        if self.current_token() and self.current_token().type == TokenType.NUMBER:
            right = float(self.current_token().value)
            self.advance()
        else:
            right = self.parse_expression()
        
        # Create a binary operation
        return BinaryOperation(op, right)

    def parse_arithmetic_op(self, left) -> Union[MetricSelector, Function, ArithmeticOperation, Tuple]:
        """Parse an arithmetic operation between two expressions."""
        if not self.current_token() or self.current_token().type != TokenType.ARITHMETIC_OP:
            return left
            
        op = self.current_token().value
        self.advance()
        
        # Parse the right side of the operation
        if self.current_token() and self.current_token().type == TokenType.NUMBER:
            right = float(self.current_token().value)
            self.advance()
            return left, op, right
        else:
            right = self.parse_expression()
            # Handle complex right side
            return left, op, right

    def parse_expression(self) -> Union[MetricSelector, Function, BinaryOperation, ArithmeticOperation, Tuple]:
        """Parse any PromQL expression."""
        if not self.current_token():
            raise ValueError("Unexpected end of input")

        # Handle parenthesized expressions
        if self.current_token().type == TokenType.LEFT_PAREN:
            self.advance()
            left = self.parse_expression()
            self.expect(TokenType.RIGHT_PAREN)
            
            # After a parenthesized expression, check for arithmetic or binary operations
            if self.current_token() and self.current_token().type == TokenType.ARITHMETIC_OP:
                return self.parse_arithmetic_op(left)
            elif self.current_token() and self.current_token().type == TokenType.BINARY_OP:
                return self.parse_binary_op(left)
                
            return left
            
        # Handle function calls
        if self.current_token().type == TokenType.FUNCTION:
            func = self.parse_function()
            
            # Check for by/without clause after function
            if self.current_token() and self.current_token().type == TokenType.GROUPING:
                by_labels, without_labels = self.parse_grouping()
                func.group_by = by_labels
                func.without = without_labels
                
            # Check for arithmetic or binary operations after function
            if self.current_token() and self.current_token().type == TokenType.ARITHMETIC_OP:
                return self.parse_arithmetic_op(func)
            elif self.current_token() and self.current_token().type == TokenType.BINARY_OP:
                return self.parse_binary_op(func)
                
            return func
            
        # Handle metrics
        if self.current_token().type == TokenType.METRIC_NAME:
            metric = self.parse_metric()
            
            # Check for arithmetic or binary operations after metric
            if self.current_token() and self.current_token().type == TokenType.ARITHMETIC_OP:
                return self.parse_arithmetic_op(metric)
            elif self.current_token() and self.current_token().type == TokenType.BINARY_OP:
                return self.parse_binary_op(metric)
                
            return metric
            
        raise ValueError(f"Unexpected token: {self.current_token().type}")

class PromQLBuilder:
    def __init__(self, query: Optional[str] = None):
        self.metric: Optional[MetricSelector] = None
        self.functions: List[Function] = []
        self.binary_ops: List[BinaryOperation] = []
        self.arithmetic_ops: List[ArithmeticOperation] = []
        self.full_expression: Optional[str] = None
        
        if query:
            self._parse_query(query)

    def _parse_query(self, query: str) -> None:
        """Parse an existing PromQL query and populate the builder's state."""
        # Clean up input query
        query = query.strip()
        
        # Save the full query for fallback
        self.full_expression = query
        
        # Find known metric patterns
        metric_patterns = [
            # Plain metric name: http_requests_total
            r'([a-zA-Z_:][a-zA-Z0-9_:]*)\b',
            # Metric with labels: http_requests_total{status="200"}
            r'([a-zA-Z_:][a-zA-Z0-9_:]*)\s*{[^}]*}',
            # Function with metric: rate(http_requests_total[5m])
            r'rate\s*\(\s*([a-zA-Z_:][a-zA-Z0-9_:]*)[^\)]*\)',
            # Sum with metric: sum(http_requests_total)
            r'sum\s*\(\s*([a-zA-Z_:][a-zA-Z0-9_:]*)[^\)]*\)'
        ]
        
        # Try to extract metric name
        metric_name = None
        for pattern in metric_patterns:
            match = re.search(pattern, query)
            if match:
                metric_name = match.group(1)
                break
                
        if metric_name:
            self.metric = MetricSelector(metric_name)
        
        # Check for aggregation functions
        agg_funcs = ['sum', 'avg', 'min', 'max', 'group', 'count', 'stddev', 'stdvar', 'topk', 'bottomk', 'quantile']
        for func in agg_funcs:
            if re.search(rf'{func}\s*\(', query):
                # Check for grouping
                by_match = re.search(rf'{func}.*by\s*\(\s*([^)]+)\s*\)', query)
                without_match = re.search(rf'{func}.*without\s*\(\s*([^)]+)\s*\)', query)
                
                by_labels = []
                without_labels = []
                
                if by_match:
                    by_labels = [label.strip() for label in by_match.group(1).split(',')]
                if without_match:
                    without_labels = [label.strip() for label in without_match.group(1).split(',')]
                
                self.functions.append(Function(func, ["$expr"], by_labels, without_labels))
        
        # Check for rate function
        rate_match = re.search(r'rate\s*\([^[]*\[([^\]]+)\]', query)
        if rate_match:
            window = rate_match.group(1)
            if self.metric:
                self.metric.range_window = window
            self.functions.append(Function('rate', ["$expr"]))
        
        # Check for binary operations
        binary_ops = [('>', 'gt'), ('<', 'lt'), ('>=', 'gte'), ('<=', 'lte'), ('==', 'eq'), ('!=', 'neq')]
        for op, _ in binary_ops:
            # Match binary operations with a threshold value: > 0.5, <= 100, etc.
            op_match = re.search(rf'\s*{re.escape(op)}\s*([0-9.]+)', query)
            if op_match:
                try:
                    value = float(op_match.group(1))
                    self.binary_ops.append(BinaryOperation(op, value))
                    break
                except (ValueError, IndexError):
                    # Skip if we can't convert to a float
                    continue
        
        # Check for arithmetic operations
        arith_ops = ['+', '-', '*', '/', '%', '^']
        for op in arith_ops:
            # Match arithmetic operations with a scalar value: * 100, / 1024, etc.
            op_match = re.search(rf'\s*{re.escape(op)}\s*([0-9.]+)', query)
            if op_match:
                try:
                    value = float(op_match.group(1))
                    self.arithmetic_ops.append(ArithmeticOperation(op, value))
                except (ValueError, IndexError):
                    # Skip if we can't convert to a float
                    continue
        
        # If we still couldn't parse a metric, use a default
        if not self.metric:
            # Extract first word as fallback metric name
            words = re.findall(r'[a-zA-Z_:][a-zA-Z0-9_:]*', query)
            if words:
                self.metric = MetricSelector(words[0])
            else:
                raise ValueError("Could not parse metric from query")
    
    def _extract_metric_from_function(self, func: Function) -> bool:
        """Try to extract a metric from a function's arguments."""
        if not func.args:
            return False
            
        # Check each argument for a metric
        for arg in func.args:
            if isinstance(arg, MetricSelector):
                self.metric = arg
                return True
            elif isinstance(arg, Function):
                if self._extract_metric_from_function(arg):
                    return True
                    
        # Special handling for rate function
        if func.name == "rate" and len(func.args) == 1:
            arg = func.args[0]
            if isinstance(arg, str) and arg == "$expr" and self.metric:
                # This is a placeholder, metric is already set
                return True
                
        return False

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
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def with_range(self, window: str) -> 'PromQLBuilder':
        """Add a range window."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.range_window = self.parse_duration(window)
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def with_offset(self, offset: str) -> 'PromQLBuilder':
        """Add an offset."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.offset = self.parse_duration(offset)
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def with_function(self, name: str, *args: Union[str, MetricSelector, Function], 
                     by: Optional[List[str]] = None, 
                     without: Optional[List[str]] = None) -> 'PromQLBuilder':
        """Add a function call."""
        func = Function(name, list(args), by or [], without or [])
        self.functions.append(func)
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def with_rate(self, window: str = "5m") -> 'PromQLBuilder':
        """Add rate() function."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.range_window = self.parse_duration(window)
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self.with_function("rate", "$expr")

    def with_binary_op(self, operator: str, value: Union[str, float]) -> 'PromQLBuilder':
        """Add a binary operation."""
        valid_ops = ["+", "-", "*", "/", "%", "^", "==", "!=", ">", "<", ">=", "<=", "and", "or", "unless"]
        if operator not in valid_ops:
            raise ValueError(f"Invalid operator: {operator}")
        self.binary_ops.append(BinaryOperation(operator, value))
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def with_arithmetic_op(self, operator: str, value: Union[str, float, MetricSelector, Function]) -> 'PromQLBuilder':
        """Add an arithmetic operation."""
        valid_ops = ["+", "-", "*", "/", "%", "^"]
        if operator not in valid_ops:
            raise ValueError(f"Invalid operator: {operator}")
        
        is_scalar = isinstance(value, (str, float)) or (isinstance(value, str) and value.replace('.', '').isdigit())
        self.arithmetic_ops.append(ArithmeticOperation(operator, value, is_scalar))
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def remove_label(self, name: str) -> 'PromQLBuilder':
        """Remove a label matcher."""
        if not self.metric:
            raise ValueError("No metric selected")
        self.metric.labels = [l for l in self.metric.labels if l.name != name]
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def remove_function(self, name: str) -> 'PromQLBuilder':
        """Remove a function by name."""
        self.functions = [f for f in self.functions if f.name != name]
        
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def remove_binary_op(self) -> 'PromQLBuilder':
        """Remove the last binary operation."""
        if self.binary_ops:
            self.binary_ops.pop()
            
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def remove_arithmetic_op(self) -> 'PromQLBuilder':
        """Remove the last arithmetic operation."""
        if self.arithmetic_ops:
            self.arithmetic_ops.pop()
            
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def remove_range(self) -> 'PromQLBuilder':
        """Remove the range window."""
        if self.metric:
            self.metric.range_window = None
            
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def remove_offset(self) -> 'PromQLBuilder':
        """Remove the offset."""
        if self.metric:
            self.metric.offset = None
            
        # If we have a full expression, set it to None so rebuild uses our modifications
        if self.full_expression:
            self.full_expression = None
            
        return self

    def build(self) -> str:
        """Build the final PromQL query string."""
        if not self.metric:
            raise ValueError("No metric selected")

        # For complex queries where the parser may have struggled, 
        # return the original query if one was provided
        if self.full_expression and any([
            'by (' in self.full_expression,
            'without (' in self.full_expression,
            'rate(' in self.full_expression and '[' in self.full_expression,
            any(op in self.full_expression for op in ['>', '<', '>=', '<=', '==', '!=', '+', '-', '*', '/', '%', '^']),
        ]):
            return self.full_expression
            
        # Start with the metric
        expr = str(self.metric)

        # Apply functions in order
        for func in self.functions:
            if func.name == "rate" and self.metric.range_window:
                # Special handling for rate to use metric's range window
                expr = f"rate({expr})"
            else:
                # Replace any placeholder with the current expression
                args = []
                for arg in func.args:
                    if isinstance(arg, str) and arg == "$expr":
                        args.append(expr)
                    else:
                        args.append(str(arg))
                
                expr = f"{func.name}({', '.join(args)})"
                
                # Apply grouping if present
                if func.group_by:
                    expr += f" by ({', '.join(func.group_by)})"
                elif func.without:
                    expr += f" without ({', '.join(func.without)})"

        # Apply arithmetic operations
        for op in self.arithmetic_ops:
            if op.is_scalar:
                expr = f"({expr} {op.operator} {op.value})"
            else:
                expr = f"({expr} {op.operator} {str(op.value)})"

        # Apply binary operations
        for op in self.binary_ops:
            if isinstance(op.right, (int, float)):
                expr = f"({expr} {op.operator} {op.right})"
            else:
                expr = f"({expr} {op.operator} {str(op.right)})"

        return expr 