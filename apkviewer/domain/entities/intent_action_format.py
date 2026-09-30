"""
Single definition of the text format used to carry an exported intent
action across layers: "action ( key='value', ... )".

The producer (which reads the manifest) and the consumer (which shows the
details of one action) both use this class, so the format is a documented
contract instead of an implicit agreement between two layers.
"""

from collections.abc import Sequence


class IntentActionFormat:
    _OPENING: str = " ( "
    _CLOSING: str = " )"

    @staticmethod
    def format_extra(key: str, value: str) -> str:
        return f"{key}='{value}'"

    @classmethod
    def format(cls, action: str, extras: Sequence[str]) -> str:
        return f"{action}{cls._OPENING}{', '.join(extras)}{cls._CLOSING}"

    @classmethod
    def parse(cls, line: str) -> dict[str, str]:
        action = line
        extras_text = ""
        if cls._OPENING in action and action.endswith(cls._CLOSING):
            action, extras_text = action.split(cls._OPENING, 1)
            extras_text = extras_text[: -len(cls._CLOSING)]

        fields = {"Action": action}
        for extra in filter(None, extras_text.split(", ")):
            if "=" not in extra:
                continue
            key, value = extra.split("=", 1)
            key = key.strip().capitalize()
            value = value.strip().strip("'").strip('"')
            fields[key] = f"{fields[key]}, {value}" if key in fields else value
        return fields
