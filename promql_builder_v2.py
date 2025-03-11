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
                
            if self.current_char.isalpha() or self.current_char == '_':
                tokens.append(self.read_identifier())
                continue

            if self.current_char == '"':
                start_pos = self.pos
                value = self.read_string()
                tokens.append(Token(TokenType.LABEL_VALUE, value, start_pos))
                continue

            if self.current_char in '+-*/%^':
                tokens.append(Token(TokenType.ARITHMETIC_OP, self.current_char, self.pos))
                self.advance()
                continue

            # Add more token handling...
            if self.current_char == '{':
                tokens.append(Token(TokenType.LEFT_BRACE, '{', self.pos))
            elif self.current_char == '}':
                tokens.append(Token(TokenType.RIGHT_BRACE, '}', self.pos))
            # ... etc.

            self.advance()

        return tokens

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

    def parse_function(self) -> Function:
        name = self.expect(TokenType.FUNCTION).value
        self.expect(TokenType.LEFT_PAREN)
        args = self.parse_function_args()
        self.expect(TokenType.RIGHT_PAREN)

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

    def parse_function_args(self) -> List[str]:
        args = []
        while True:
            arg = self.parse_expression()
            args.append(arg)
            if not self.match(TokenType.COMMA):
                break
        return args

    def parse_label_list(self) -> List[str]:
        labels = []
        while True:
            labels.append(self.expect(TokenType.LABEL_NAME).value)
            if not self.match(TokenType.COMMA):
                break
        return labels

class PromQLBuilder:
    def __init__(self, query: Optional[str] = None):
        self.metric: Optional[MetricSelector] = None
        self.functions: List[Function] = []
        self.binary_ops: List[tuple[str, Union[str, float]]] = []
        self.arithmetic_ops: List[ArithmeticOperation] = []
        
        if query:
            self._parse_query(query)

    def _parse_query(self, query: str) -> None:
        lexer = Lexer(query)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        
        # Parse the query and populate the builder's state
        # Implementation here...

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