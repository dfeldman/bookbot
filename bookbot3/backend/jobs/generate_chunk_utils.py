"""
Utilities for the GenerateChunkJob.
"""

import re

def resolve_template_variables(template_string: str, placeholder_values: dict) -> str:
    """
    Resolves placeholder variables in a template string.

    Args:
        template_string: The string containing placeholders like {{variable}}.
        placeholder_values: A dictionary mapping variable names to their values.

    Returns:
        The template string with all placeholders replaced.
    """
    if not template_string:
        return ""

    def replace_match(match):
        variable_name = match.group(1).strip()
        return placeholder_values.get(variable_name, match.group(0))

    return re.sub(r"{{\s*(\w+)\s*}}", replace_match, template_string)
