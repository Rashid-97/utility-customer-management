# Unit Testing Guide

The unit suite covers Domain behavior and Application orchestration. Tests stay deterministic and do not require PostgreSQL, HTTP servers, or external services.

## Naming

Use:

```text
test__method_name__when_condition__should_expected_result
```

A test name should identify the behavior, scenario, and expected outcome.

## Arrange, Act, Assert

Every test contains the three explicit sections in order:

```python
def test__create__when_input_is_valid__should_return_value():
    # Arrange
    value = "valid"

    # Act
    result = create_value(value)

    # Assert
    assert result is not None
```

For failures, place `pytest.raises(...)` in the Act section and assert a meaningful exception attribute, message, state, or interaction in Assert.

## Test the public contract

Prefer assertions on:

- returned result fields;
- aggregate or entity state;
- expected exceptions;
- recorded Domain Events when the behavior emits them;
- required dependency calls or absence of writes on failure.

Do not assert private implementation details or incidental call order.

## Domain tests

Use real entities and value objects. Exercise state changes through public aggregate methods and do not bypass invariants to create test data.

Keep simple Domain tests as plain functions unless shared setup makes a class clearer.

## Application tests

Construct handlers with mocked ports and Unit of Work dependencies. Use `Mock` or `MagicMock` with the real interface as the spec.

A test class may use `setup_method()` and `self.sut` when several scenarios share handler wiring. Each test must receive fresh mutable dependencies.

Do not call live Identity, GIS, Billing, PostgreSQL, or HTTP services.

## Test data

Factories should:

- create valid objects by default;
- allow scenario-specific overrides;
- keep important values visible in the test;
- use deterministic IDs and times when assertions depend on them;
- never execute the behavior under test.

Use descriptive constants for values with business meaning. Avoid constants that only rename obvious values such as `True`, `None`, `0`, or `1`.

## Parameterization

Use `pytest.mark.parametrize` when several inputs have the same setup, behavior, and assertions. Keep separate tests when scenarios have different business meaning, side effects, or errors.

## Failure contract

This project uses exceptions for expected Domain and Application failures. Tests should assert the real exception type with `pytest.raises`.

Do not introduce Result wrappers or change production contracts for test convenience.

## Scope

Unit tests do not verify:

- SQLAlchemy mappings or database constraints;
- Alembic migrations;
- FastAPI routing;
- live external integrations.

Those concerns require integration or end-to-end tests. Run the unit suite with:

```sh
python -m pytest
```
