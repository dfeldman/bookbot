"""
Utilities for the GenerateChunkJob.
"""

import re

def resolve_template_variables(template_string: str, placeholder_values: dict) -> str:
    """
    Resolves placeholder variables in a template string.

    Supports standard replacement `{{ variable }}` and conditional replacement
    `{{ prefix | variable }}`. The conditional form only renders if the
    variable has a non-empty value.

    Args:
        template_string: The string containing placeholders.
        placeholder_values: A dictionary mapping variable names to their values.

    Returns:
        The template string with all placeholders replaced.
    """
    if not template_string:
        return ""

    def replace_match(match):
        # Full content inside {{...}}, e.g., "prefix | variable" or "variable"
        content = match.group(1).strip()

        if "|" in content:
            # Conditional replacement: {{ prefix | variable }}
            parts = content.split("|", 1)
            prefix = parts[0]
            variable_name = parts[1].strip()
            
            value = placeholder_values.get(variable_name)
            
            # Only render if value is not None and not an empty string
            if value:
                return prefix + str(value)
            else:
                return ""
        else:
            # Standard replacement: {{ variable }}
            variable_name = content
            value = placeholder_values.get(variable_name)
            return str(value) if value is not None else match.group(0)

    # Regex to find {{...}} patterns, capturing the content inside.
    # Handles multi-line content with re.DOTALL.
    return re.sub(r"{{\s*(.*?)\s*}}", replace_match, template_string, flags=re.DOTALL)
