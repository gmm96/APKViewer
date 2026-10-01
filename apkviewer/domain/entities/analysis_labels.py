"""
Section titles and field labels that producers (infrastructure) and
consumers (presentation) of the analysis sections must agree on. They live
in the domain so neither side has to import the other to share them.
"""

# --- Section titles (each tab decides which of them it displays) ---
SECTION_APP_INFO: str = "App Information"
SECTION_SECURITY: str = "Permissions & Signing"
SECTION_THIRD_PARTY: str = "Third-party Code"
SECTION_COMPONENTS: str = "Declared Components"
SECTION_INTENTS: str = "Exported Intents"

# --- Field labels ---
FIELD_CERTIFICATES: str = "Certificates"
FIELD_INTENT_ACTIONS: str = "Intent Actions"
