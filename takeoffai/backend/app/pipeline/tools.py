"""Phase 3 Agent Tools — tool definitions for the orchestrator LLM.

These follow the Anthropic tool_use schema. The agent calls these tools
during refinement to re-inspect areas, validate patterns, and finalize.
"""

TOOL_DEFINITIONS = [
    {
        "name": "crop_and_inspect",
        "description": (
            "Crop a specific region of the drawing at high resolution and detect fixtures. "
            "Use this to re-inspect boundary zones, low-confidence areas, or suites where "
            "fixtures are expected but missing. Each call costs 1 VLM call from your budget."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x_pct": {
                    "type": "number",
                    "description": "Center X of crop as percentage of page width (0-100)",
                },
                "y_pct": {
                    "type": "number",
                    "description": "Center Y of crop as percentage of page height (0-100)",
                },
                "width_pct": {
                    "type": "number",
                    "description": "Width of crop as percentage of page (5-50)",
                },
                "height_pct": {
                    "type": "number",
                    "description": "Height of crop as percentage of page (5-50)",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this region needs re-inspection",
                },
            },
            "required": ["x_pct", "y_pct", "width_pct", "height_pct", "reason"],
        },
    },
    {
        "name": "validate_pattern",
        "description": (
            "Check detection counts against expected domain patterns. "
            "Use 'suite_kitchen' to verify each suite has expected kitchen fixtures. "
            "Use 'corridor' to check corridor fixture symmetry and consistency. "
            "Returns which suites/areas have missing or unexpected counts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_type": {
                    "type": "string",
                    "enum": ["suite_kitchen", "corridor", "all"],
                    "description": "Which pattern to validate",
                },
            },
            "required": ["pattern_type"],
        },
    },
    {
        "name": "get_current_state",
        "description": (
            "Get a summary of all detections so far: counts by label, room, confidence, "
            "boundary flags, and VLM budget remaining."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "finalize",
        "description": (
            "Declare detection complete. Call this when you are confident the count is "
            "accurate or you have exhausted useful re-inspection opportunities."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of findings and confidence level",
                },
            },
            "required": ["summary"],
        },
    },
]
