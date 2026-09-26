"""
Resolves a path relative to the app's bundled assets (icons, etc.),
working both when run from source and when frozen into a single
compiled executable (Nuitka onefile extracts to a temp dir at runtime).
"""

import os
import sys


class AssetPathResolver:
    def resolve(self, relative_path: str) -> str:
        # sys.modules['__main__'].__file__ always points at the entry
        # script (main.py): the project root in development, or Nuitka's
        # extracted temp directory when running as a frozen executable.
        main_file = sys.modules["__main__"].__file__
        assert main_file is not None

        base_path = os.path.dirname(os.path.abspath(main_file))
        return os.path.join(base_path, relative_path)
