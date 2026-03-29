#!/bin/bash
pipx install vrg
pip install vrg
uv tool install vrg
xattr -d com.apple.quarantine ./vrg
vrg --version

# 1. Configure credentials
vrg configure setup

# 2. Verify connection
vrg system info

# 3. List your VMs
vrg vm list

vrg <command> --help

vrg vm create -f web-server.vrg.yaml --dry-run   # Preview
vrg vm create -f web-server.vrg.yaml              # Create
