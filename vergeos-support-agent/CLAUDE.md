# VergeOS Support Agent

A customer support chatbot for the verge.io VergeOS infrastructure platform, built with the Claude Agent SDK.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python agent.py
```

## Project Structure

- `agent.py` — Main support agent (interactive terminal chatbot)
- `requirements.txt` — Python dependencies
- `CLAUDE.md` — This file

## What it supports

- VergeOS platform questions (install, config, upgrades)
- Virtual Data Center (vDC) setup and management
- Networking — VLANs, VPNs, software-defined firewalls
- Storage — NAS, vSAN, snapshots, replication
- VMware migration to VergeOS
- HA/DR — cluster config, cloud snapshots
