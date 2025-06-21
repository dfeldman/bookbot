import pytest
from backend.jobs.generate_chunk_utils import resolve_template_variables

def test_resolve_template_variables_simple_replacement():
    """Test basic placeholder replacement."""
    template = "Hello, {{ name }}!"
    values = {"name": "World"}
    expected = "Hello, World!"
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_multiple_replacements():
    """Test multiple placeholders."""
    template = "The quick {{ color }} {{ animal }} jumps over the lazy dog."
    values = {"color": "brown", "animal": "fox"}
    expected = "The quick brown fox jumps over the lazy dog."
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_with_whitespace():
    """Test placeholders with extra whitespace."""
    template = "Hello, {{  name  }}!"
    values = {"name": "Whitespace"}
    expected = "Hello, Whitespace!"
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_missing_variable():
    """Test when a variable is missing from the values dict."""
    template = "Hello, {{ name }}! Your id is {{ user_id }}."
    values = {"name": "Test"}
    expected = "Hello, Test! Your id is {{ user_id }}."
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_no_variables():
    """Test a template with no variables."""
    template = "This is a plain string."
    values = {"name": "Test"}
    expected = "This is a plain string."
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_empty_template():
    """Test with an empty template string."""
    template = ""
    values = {"name": "Test"}
    expected = ""
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_empty_values():
    """Test with an empty values dictionary."""
    template = "Hello, {{ name }}!"
    values = {}
    expected = "Hello, {{ name }}!"
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_numeric_values():
    """Test with numeric values that should be handled as strings."""
    template = "Value: {{ num }}"
    values = {"num": "123"}
    expected = "Value: 123"
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_with_special_chars_in_value():
    """Test when the replacement value has special characters."""
    template = "Special chars: {{ special }}"
    values = {"special": "$^*(){}"}
    expected = "Special chars: $^*(){}"
    assert resolve_template_variables(template, values) == expected

def test_resolve_template_variables_malformed_placeholders():
    """Test malformed placeholders that shouldn't be replaced."""
    template = "Malformed: {{ name }, { name }}, {{name"
    values = {"name": "Test"}
    expected = "Malformed: {{ name }, { name }}, {{name"
    assert resolve_template_variables(template, values) == expected
