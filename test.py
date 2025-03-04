import re
from pyconfig import *

# --- Combined Test Suite ---
def run_all_tests(test_cases = {}):
    def make_getter(env):
        def getter(key: str):
            return env.get(key.upper())
        return getter
    
    passed = 0
    failed = 0
    print("=== Running Combined Tests ===")
    for i, tc in enumerate(test_cases):
        expr = tc["expr"]
        env = tc["env"]
        getter = make_getter(env)
        try:
            tokens = tokenize(expr)
            if not tokens:
                raise ValueError("Empty expression")
            postfix = shunting_yard(tokens)
            parser = BooleanExpressionParser(getter=getter)
            result = parser.evaluate_postfix(postfix)
            if result == tc["expected"]:
                print(f"Test {i+1} Passed: {tc['description']}")
                passed += 1
            else:
                print(f"Test {i+1} Failed: {tc['description']}\n  Expression: {expr}\n  Expected: {tc['expected']}, Got: {result}")
                failed += 1
        except Exception as e:
            print(f"Test {i+1} Exception: {tc['description']}\n  Expression: {expr}\n  Exception: {e}")
            failed += 1
    print(f"\n=== Combined Test Results ===")
    print(f"Total tests passed: {passed}")
    print(f"Total tests failed: {failed}")

if __name__ == "__main__":
    run_all_tests(test_cases = [
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
        {"description": "String comparison false", "expr": "A=='test'", "env": {"A": "exam"}, "expected": False},
        {"description": "Numeric comparison with string literal (should be False)", "expr": "A=='1'", "env": {"A": 1}, "expected": False},
        {"description": "Deeply nested expressions", "expr": "A && (B || (C && (D || (!E && F))))", "env": {"A": True, "B": False, "C": True, "D": False, "E": False, "F": True}, "expected": True},
        {"description": "Deeply nested with multiple negations", "expr": "!(!A && (B || !!C))", "env": {"A": True, "B": False, "C": False}, "expected": True},
        # Additional advanced tests
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
        # Complex dependency expression tests
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
        }
    ])
