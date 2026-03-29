#!/bin/bash
pipx install vrg
pip install vrg
uv tool install vrg
xattr -d com.apple.quarantine ./vrg
vrg --version
