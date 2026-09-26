"""
Turns a formatted "action ( key='value', ... )" line back into a dict.
"""


class IntentActionParser:
    def parse(self, line_text: str) -> dict:
        action = line_text
        extras_str = ""

        if " ( " in action and action.endswith(" )"):
            action, extras_str = action.split(" ( ", 1)
            extras_str = extras_str[:-2]

        fields = {"Action": action}

        if extras_str:
            for extra in extras_str.split(", "):
                if "=" not in extra:
                    continue
                key, value = extra.split("=", 1)
                key = key.strip().capitalize()
                value = value.strip().strip("'").strip('"')

                if key in fields:
                    fields[key] += f", {value}"
                else:
                    fields[key] = value

        return fields
