---
applyTo: "tests/**"
---
# Test File Instructions

- Use pytest fixtures from conftest.py for test setup, not setUp/tearDown methods
- Every test function should have a clear, descriptive name: `test_<what>_<condition>_<expected>`
- Use hypothesis for property-based tests when testing functions with numeric, string, or collection inputs
- Use pytest.raises for exception testing with a match pattern
- Use pytest-subprocess (fp fixture) for mocking subprocess calls
- Maintain 80% minimum branch coverage — check with `make test`
- Use tmp_path fixture for temporary files, not hardcoded /tmp paths
- Parametrize related test cases with @pytest.mark.parametrize
