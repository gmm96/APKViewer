"""
Entry point for the APKViewer desktop application.

Usage:
    python main.py [path/to/app.apk]
"""

import sys
import tkinter

from apkviewer.presentation import ApkAnalyzerApp


def main():
    root: tkinter.Tk = tkinter.Tk()
    app: ApkAnalyzerApp = ApkAnalyzerApp(root)

    if len(sys.argv) > 1:
        root.after(100, lambda: app.start_analysis(sys.argv[1]))

    root.mainloop()


if __name__ == "__main__":
    main()
