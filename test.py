import re
from pyconfix import (
    tokenize,
    shunting_yard,
    BooleanExpressionParser,
    ConfigOption,
    OptionManager,
)

# -------------------------------
# Helper Assertion Functions
# -------------------------------
def assert_equal(actual, expected, message=""):
    if actual != expected:
        raise AssertionError(f"{message} Expected {expected}, got {actual}")

def assert_raises(func, expected_exception_substr, message=""):
    try:
        func()
    except Exception as e:
        if expected_exception_substr not in str(e):
            raise AssertionError(
                f"{message} Expected exception containing '{expected_exception_substr}', but got '{e}'"
            )
        return  # Passed
    raise AssertionError(f"{message} Expected exception containing '{expected_exception_substr}', but no exception was raised")

def run_test_suite(test_cases, test_func, suite_name):
    passed = 0
    failed = 0
    print(f"=== Running {suite_name} ===")
    for i, tc in enumerate(test_cases, 1):
        description = tc.get("description", f"Test {i}")
        try:
            test_func(tc)
        except AssertionError as e:
            print(f"Test {i} Failed: {description}\n  {e}")
            failed += 1
        else:
            print(f"Test {i} Passed: {description}")
            passed += 1
    print(f"\n=== {suite_name} Results ===")
    print(f"Total tests passed: {passed}")
    print(f"Total tests failed: {failed}")
    return passed, failed

# -------------------------------
# Boolean Expression Test Suite
# -------------------------------
def run_boolean_expression_test_case(tc):
    def run_expr():
        tokens = tokenize(tc["expr"])
        if not tokens:
            raise ValueError("Empty tokens")
        postfix = shunting_yard(tokens)
        getter = lambda key: tc.get("env", {}).get(key.upper())
        parser = BooleanExpressionParser(getter=getter)
        return parser.evaluate_postfix(postfix)
    expected_exception = tc.get("expected_exception")
    if expected_exception:
        assert_raises(run_expr, expected_exception, f"Expression: {tc['expr']}")
    else:
        result = run_expr()
        assert_equal(result, tc["expected"], f"Expression: {tc['expr']}")

boolean_expression_tests = [
        # Basic tests
        {"description": "Single variable true", "expr": "A", "env": {"A": True}, "expected": True},
        {"description": "Single variable false", "expr": "A", "env": {"A": False}, "expected": False},
        {"description": "NOT operator with true", "expr": "!A", "env": {"A": True}, "expected": False},
        {"description": "NOT operator with false", "expr": "!A", "env": {"A": False}, "expected": True},
        {"description": "Chained NOT operators", "expr": "!!!A", "env": {"A": True}, "expected": False},
        {"description": "AND operator true", "expr": "A && B", "env": {"A": True, "B": True}, "expected": True},
        {"description": "AND operator false (one false)", "expr": "A && B", "env": {"A": True, "B": False}, "expected": False},
        {"description": "OR operator true", "expr": "A || B", "env": {"A": False, "B": True}, "expected": True},
        {"description": "OR operator false", "expr": "A || B", "env": {"A": False, "B": False}, "expected": False},
        {"description": "Equality operator true (numeric)", "expr": "A == B", "env": {"A": 1, "B": 1}, "expected": True},
        {"description": "Equality operator false (numeric)", "expr": "A == B", "env": {"A": 1, "B": 2}, "expected": False},
        {"description": "Inequality operator true (numeric)", "expr": "A != B", "env": {"A": 1, "B": 2}, "expected": True},
        {"description": "Inequality operator false (numeric)", "expr": "A != B", "env": {"A": 1, "B": 1}, "expected": False},
        {"description": "Greater than true", "expr": "A > B", "env": {"A": 3, "B": 2}, "expected": True},
        {"description": "Greater than false", "expr": "A > B", "env": {"A": 2, "B": 3}, "expected": False},
        {"description": "Less than true", "expr": "A < B", "env": {"A": 2, "B": 3}, "expected": True},
        {"description": "Less than false", "expr": "A < B", "env": {"A": 3, "B": 2}, "expected": False},
        {"description": "Greater than or equal true", "expr": "A >= B", "env": {"A": 3, "B": 3}, "expected": True},
        {"description": "Greater than or equal false", "expr": "A >= B", "env": {"A": 2, "B": 3}, "expected": False},
        {"description": "Less than or equal true", "expr": "A <= B", "env": {"A": 2, "B": 3}, "expected": True},
        {"description": "Less than or equal false", "expr": "A <= B", "env": {"A": 4, "B": 3}, "expected": False},
        {"description": "Parentheses grouping", "expr": "A && (B || C)", "env": {"A": True, "B": False, "C": True}, "expected": True},
        {"description": "Nested parentheses", "expr": "(A && (B || C)) || D", "env": {"A": True, "B": False, "C": False, "D": True}, "expected": True},
        {"description": "Precedence: A || B && C", "expr": "A || B && C", "env": {"A": False, "B": True, "C": False}, "expected": False},
        {"description": "Precedence: (A || B) && C", "expr": "(A || B) && C", "env": {"A": False, "B": True, "C": True}, "expected": True},
        {"description": "Case insensitive variable lookup", "expr": "Log_Level=='DEBUG'", "env": {"LOG_LEVEL": "DEBUG"}, "expected": True},
        {"description": "Quoted string equality true", "expr": "A=='hello world'", "env": {"A": "hello world"}, "expected": True},
        {"description": "String comparison false", "expr": "A=='test'", "env": {"A": "exam"}, "expected": False},
        {"description": "Numeric comparison with string literal (should be False)", "expr": "A=='1'", "env": {"A": 1}, "expected": False},
        {"description": "Deeply nested expressions", "expr": "A && (B || (C && (D || (!E && F))))", "env": {"A": True, "B": False, "C": True, "D": False, "E": False, "F": True}, "expected": True},
        {"description": "Deeply nested with multiple negations", "expr": "!(!A && (B || !!C))", "env": {"A": True, "B": False, "C": False}, "expected": True},
        {"description": "Chain of AND operators (all true)", "expr": "A && B && C && D && E", "env": {"A": True, "B": True, "C": True, "D": True, "E": True}, "expected": True},
        {"description": "Chain of AND operators (one false)", "expr": "A && B && C && D && E", "env": {"A": True, "B": True, "C": False, "D": True, "E": True}, "expected": False},
        {"description": "Extra parentheses around single variable (true)", "expr": "(((A)))", "env": {"A": True}, "expected": True},
        {"description": "Extra parentheses around single variable (false)", "expr": "(((A)))", "env": {"A": False}, "expected": False},
        {"description": "Numeric literal AND numeric literal (1 && 0)", "expr": "1 && 0", "env": {}, "expected": False},
        {"description": "Numeric literal OR numeric literal (1 || 0)", "expr": "1 || 0", "env": {}, "expected": True},
        {"description": "Numeric literal AND NOT numeric literal (1 && !0)", "expr": "1 && !0", "env": {}, "expected": True},
        {"description": "Deeply nested group with redundant parentheses", "expr": "(((((A && B)))))", "env": {"A": True, "B": True}, "expected": True},
        {"description": "Complex nested expression with mixed groups", "expr": "A && (B || (C && (D || (E && F))) )", "env": {"A": True, "B": False, "C": True, "D": False, "E": True, "F": True}, "expected": True},
        {"description": "Long OR chain with one true", "expr": "A || B || C || D || E || F || G || H || I || J", "env": {"A": False, "B": False, "C": False, "D": False, "E": False, "F": False, "G": False, "H": False, "I": False, "J": True}, "expected": True},
        {"description": "Long OR chain all false", "expr": "A || B || C || D || E || F || G || H || I || J", "env": {"A": False, "B": False, "C": False, "D": False, "E": False, "F": False, "G": False, "H": False, "I": False, "J": False}, "expected": False},
        {"description": "Multiple negations (even number) on variable", "expr": "!!!!A", "env": {"A": True}, "expected": True},
        {"description": "Multiple negations (odd number) on variable", "expr": "!!!!!A", "env": {"A": True}, "expected": False},
        {"description": "Equality comparison with integer literal", "expr": "A == 10", "env": {"A": 10}, "expected": True},
        {"description": "Equality comparison with float literal", "expr": "A == 10.0", "env": {"A": 10}, "expected": True},
        {"description": "Inequality comparison (A != 10) with A=5", "expr": "A != 10", "env": {"A": 5}, "expected": True},
        {"description": "Range check with numeric comparisons (A > 5 && A < 10)", "expr": "A > 5 && A < 10", "env": {"A": 7}, "expected": True},
        {"description": "Range check fails (A > 5 && A < 10) with A=5", "expr": "A > 5 && A < 10", "env": {"A": 5}, "expected": False},
        {"description": "Boundary check (A >= 5 && A <= 10) with A=5", "expr": "A >= 5 && A <= 10", "env": {"A": 5}, "expected": True},
        {"description": "Boundary check fails (A >= 5 && A <= 10) with A=11", "expr": "A >= 5 && A <= 10", "env": {"A": 11}, "expected": False},
        {"description": "Long combined expression", "expr": "A && (B || (C && D)) && (E || F) && (G || (H && I))", "env": {"A": True, "B": False, "C": True, "D": True, "E": False, "F": True, "G": False, "H": True, "I": True}, "expected": True},
        {"description": "Very deeply nested chain", "expr": "A && (B || (C && (D || (E && (F || G)))))", "env": {"A": True, "B": False, "C": True, "D": False, "E": True, "F": False, "G": True}, "expected": True},
        {"description": "Decimal comparison true", "expr": "PI == 3.14", "env": {"PI": 3.14}, "expected": True},
        {"description": "Decimal comparison false", "expr": "PI == 3.1415", "env": {"PI": 3.14}, "expected": False},
        {"description": "Combined boolean and string condition", "expr": "A && (B || !C) && (D == 'done')", "env": {"A": True, "B": False, "C": False, "D": "done"}, "expected": True},
        {"description": "Nested AND/OR with groups", "expr": "((A && B) || (!C && (D || E)))", "env": {"A": True, "B": True, "C": False, "D": False, "E": True}, "expected": True},
        {"description": "Mixed NOT with group", "expr": "A && !(B && (C || !D))", "env": {"A": True, "B": False, "C": True, "D": False}, "expected": True},
        # Advanced exact dependency expression tests
        {
            "description": "Exact expression, INTERMEDIATE_OPTION True (should be False)",
            "expr": "ENABLE_FEATURE_A && (Log_Level=='INFO' || Log_Level=='DEBUG') && !INTERMEDIATE_OPTION && (DOMAIN_ADDRESS=='localhost' || DOMAIN_ADDRESS=='hi')",
            "env": {"ENABLE_FEATURE_A": True, "LOG_LEVEL": "INFO", "INTERMEDIATE_OPTION": True, "DOMAIN_ADDRESS": "localhost"},
            "expected": False
        },
        {
            "description": "Exact expression, INTERMEDIATE_OPTION False, LogLevel DEBUG (should be True)",
            "expr": "ENABLE_FEATURE_A && (Log_Level=='INFO' || Log_Level=='DEBUG') && !INTERMEDIATE_OPTION && (DOMAIN_ADDRESS=='localhost' || DOMAIN_ADDRESS=='hi')",
            "env": {"ENABLE_FEATURE_A": True, "LOG_LEVEL": "DEBUG", "INTERMEDIATE_OPTION": False, "DOMAIN_ADDRESS": "hi"},
            "expected": True
        },
        {
            "description": "Exact expression, ENABLE_FEATURE_A False (should be False)",
            "expr": "ENABLE_FEATURE_A && (Log_Level=='INFO' || Log_Level=='DEBUG') && !INTERMEDIATE_OPTION && (DOMAIN_ADDRESS=='localhost' || DOMAIN_ADDRESS=='hi')",
            "env": {"ENABLE_FEATURE_A": False, "LOG_LEVEL": "INFO", "INTERMEDIATE_OPTION": False, "DOMAIN_ADDRESS": "localhost"},
            "expected": False
        },
        {
            "description": "Exact expression, DOMAIN_ADDRESS mismatched (should be False)",
            "expr": "ENABLE_FEATURE_A && (Log_Level=='INFO' || Log_Level=='DEBUG') && !INTERMEDIATE_OPTION && (DOMAIN_ADDRESS=='localhost' || DOMAIN_ADDRESS=='hi')",
            "env": {"ENABLE_FEATURE_A": True, "LOG_LEVEL": "DEBUG", "INTERMEDIATE_OPTION": False, "DOMAIN_ADDRESS": "example.com"},
            "expected": False
        },
        {
            "description": "Exact expression, LogLevel unexpected value (should be False)",
            "expr": "ENABLE_FEATURE_A && (Log_Level=='INFO' || Log_Level=='DEBUG') && !INTERMEDIATE_OPTION && (DOMAIN_ADDRESS=='localhost' || DOMAIN_ADDRESS=='hi')",
            "env": {"ENABLE_FEATURE_A": True, "LOG_LEVEL": "ERROR", "INTERMEDIATE_OPTION": False, "DOMAIN_ADDRESS": "localhost"},
            "expected": False
        },
        {
            "description": "Similar expression, different names (case insensitive check)",
            "expr": "FEATURE_ON && (Mode=='AUTO' || Mode=='MANUAL') && !OPTION_X && (SERVER=='prod' || SERVER=='test')",
            "env": {"FEATURE_ON": True, "MODE": "MANUAL", "OPTION_X": False, "SERVER": "prod"},
            "expected": True
        },
        {
            "description": "Similar expression, OPTION_X true makes it False",
            "expr": "FEATURE_ON && (Mode=='AUTO' || Mode=='MANUAL') && !OPTION_X && (SERVER=='prod' || SERVER=='test')",
            "env": {"FEATURE_ON": True, "MODE": "AUTO", "OPTION_X": True, "SERVER": "prod"},
            "expected": False
        },
        # Additional error/edge-case tests:
        {"description": "Mismatched parentheses (missing closing)", "expr": "A && (B || C", "env": {"A": True, "B": True, "C": False}, "expected_exception": "Mismatched parentheses"},
        {"description": "Mismatched parentheses (extra closing)", "expr": "A && B)", "env": {"A": True, "B": True}, "expected_exception": "Mismatched parentheses"},
        {"description": "Operator with missing operand (leading &&)", "expr": "&& A", "env": {"A": True}, "expected_exception": "Missing operands"},
        {"description": "Missing operand for NOT operator", "expr": "!", "env": {}, "expected_exception": "Missing operand for '!'"}, 
        {"description": "Unexpected character error", "expr": "A && #", "env": {"A": True}, "expected_exception": "Unexpected character"},
        {"description": "Variable not in environment defaults to False", "expr": "A && B", "env": {}, "expected": False},
        {"description": "Floating point with leading dot", "expr": ".5 == 0.5", "env": {}, "expected": True},
        {"description": "Expression with extra number operand", "expr": "1 2", "env": {}, "expected_exception": "extra items remain on the stack"},
        {"description": "A && !B", "expr": "A && !B", "env": {"A": True, "B": False}, "expected": True},
    ]

# -------------------------------
# ConfigOption Test Suite
# -------------------------------
def run_config_option_test_case(tc):
    # 'action' is a callable that executes the test.
    action = tc["action"]
    expected_exception = tc.get("expected_exception")
    if expected_exception:
        assert_raises(action, expected_exception, tc.get("description", ""))
    else:
        result = action()
        expected = tc.get("expected")
        # For dictionary comparisons, you might want a more robust check.
        assert_equal(result, expected, tc.get("description", ""))

config_option_tests = [
    {
        "description": "Option name cannot contain whitespace",
        "action": lambda: ConfigOption("A B", "bool"),
        "expected_exception": "cannot contain whitespace"
    },
    {
        "description": "Invalid option type",
        "action": lambda: ConfigOption("A", "invalid"),
        "expected_exception": "Invalid option type"
    },
    {
        "description": "multiple_choice default not in choices",
        "action": lambda: ConfigOption("A", "multiple_choice", default="x", choices=["a", "b"]),
        "expected_exception": "Invalid default for multiple_choice option"
    },
    {
        "description": "to_dict method works correctly",
        "action": lambda: ConfigOption("TestOpt", "int", default=10, description="A test option", dependencies="A && B").to_dict(),
        "expected": {
            "name": "TestOpt",
            "type": "int",
            "default": 10,
            "external": False,
            "data": None,
            "description": "A test option",
            "dependencies": "A && B",
            "options": [],
            "choices": [],
        }
    },
]

# -------------------------------
# OptionManager Test Suite
# -------------------------------
def setup_option_manager():
    options_data = [
        {"name": "A", "type": "bool", "default": True},
        {"name": "B", "type": "bool", "default": False, "dependencies": "A"},
        {"name": "C", "type": "int", "default": 5, "dependencies": "B"},
        {"name": "Group1", "type": "group", "options": [
            {"name": "D", "type": "string", "default": "hello"},
            {"name": "E", "type": "multiple_choice", "default": "opt1", "choices": ["opt1", "opt2"], "dependencies": "!A"}
        ]}
    ]
    m = OptionManager()
    m.options = m.parse_options(options_data)
    return m

def test_option_manager_available():
    m = setup_option_manager()
    # When A is True (default), option B should be available.
    return m.is_option_available(m.find_option("B"))

def test_option_manager_not_available():
    m = setup_option_manager()
    a = m.find_option("A")
    b = m.find_option("B")
    a.value = False
    m.reset_hidden_dependent_options()
    return m.is_option_available(b)

def run_option_manager_test_case(tc):
    result = tc["action"]()
    assert_equal(result, tc["expected"], tc.get("description", ""))

option_manager_tests = [
    {
        "description": "When A is True, B is available",
        "action": test_option_manager_available,
        "expected": True
    },
    {
        "description": "When A is False, B is not available after reset",
        "action": test_option_manager_not_available,
        "expected": False
    },
]

# -------------------------------
# Main: Run All Test Suites
# -------------------------------
if __name__ == "__main__":
    run_test_suite(boolean_expression_tests, run_boolean_expression_test_case, "Boolean Expression Tests")
    print("\n")
    run_test_suite(config_option_tests, run_config_option_test_case, "ConfigOption Tests")
    print("\n")
    run_test_suite(option_manager_tests, run_option_manager_test_case, "OptionManager Tests")
