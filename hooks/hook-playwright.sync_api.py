"""Project-local PyInstaller hook for playwright.sync_api.

Exclude bundled Chromium app payload to avoid macOS codesign failures in nested app bundles.
The runtime can still use the user's installed Playwright browser cache.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files(
    "playwright",
    excludes=["**/.local-browsers/**"],
)
