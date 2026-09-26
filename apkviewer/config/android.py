"""
Android-specific constants (manifest namespace, resource DPI priority).
"""

# --- Android manifest namespace ---
ANDROID_NS: str = "{http://schemas.android.com/apk/res/android}"

# --- DPI priority used when picking the best app icon resource ---
DPI_SCORES: dict[str, int] = {
    "xxxhdpi": 5,
    "xxhdpi": 4,
    "xhdpi": 3,
    "hdpi": 2,
    "mdpi": 1,
}
