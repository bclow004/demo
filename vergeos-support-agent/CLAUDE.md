# VergeOS Support Agent

A technical support chatbot for the verge.io VergeOS infrastructure platform.
Uses the Anthropic SDK with the **Marvin MCP server** for live VergeOS demo data.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export MARVIN_MCP_TOKEN=vrg-...    # optional — falls back to default demo token
```

## Run

```bash
python agent.py
```

## Project Structure

```
vergeos-support-agent/
├── agent.py          # Support chatbot (multi-turn, MCP-connected)
├── requirements.txt  # anthropic SDK
├── .mcp.json         # Marvin MCP server config for Claude Code
└── CLAUDE.md         # This file
```

## Architecture

- **Model**: `claude-opus-4-6` with adaptive thinking
- **MCP**: Marvin server at `https://mcp.vergeos-demo.com/mcp` — provides live
  VergeOS demo environment data (VMs, nodes, networks, storage)
- **Conversation**: Multi-turn with full history passed each request
- **Interface**: Interactive terminal chatbot; `run_support_agent()` for programmatic use

## Topics covered

| Area | Examples |
|------|---------|
| VergeOS platform | Install, config, upgrades, licensing |
| Virtual Data Centers | vDC setup, multi-tenancy, isolation |
| Networking | VLANs, VPNs, SDN firewalls |
| Storage | NAS, vSAN, snapshots, replication |
| Compute | VM management, live migration |
| VMware migration | Migration tool, VM import |
| HA/DR | Cluster config, cloud snapshots |
