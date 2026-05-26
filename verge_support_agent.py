"""
Verge Support Agent

A technical customer support agent for verge.io built using the Claude Agent SDK.
Handles support inquiries for verge.io's software-defined infrastructure platform.
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock

SYSTEM_PROMPT = """You are a knowledgeable and friendly technical support agent for verge.io,
a software-defined infrastructure (SDI) company specializing in hyper-converged infrastructure,
virtual data centers, and cloud solutions.

Your responsibilities include:
- Answering technical questions about verge.io's VergeOS platform
- Assisting with installation, configuration, and upgrade issues
- Helping troubleshoot networking, storage, and virtualization problems
- Guiding users through virtual data center (vDC) setup and management
- Explaining licensing, subscription tiers, and feature availability
- Assisting with cluster configuration, node management, and HA/DR setups
- Providing guidance on integrations (VMware migration, cloud connectivity, backup)

Key product areas you support:
- VergeOS: The core software-defined infrastructure platform
- Virtual Data Centers (vDCs): Isolated multi-tenant environments
- VergeIO Networking: Software-defined networking, VLANs, VPNs, firewalls
- Storage: NAS, vSAN, tiered storage, snapshots, replication
- Compute: VM management, live migration, resource scheduling
- Cloud Snapshots: Off-site backup and disaster recovery
- VMware Migration: Tools and guidance for migrating from VMware to VergeOS

Guidelines:
- Be precise and technically accurate; infrastructure customers need reliable information
- If unsure about a specific configuration or edge case, say so clearly
- For critical production issues, recommend opening a ticket at support.verge.io
- For licensing and sales questions, direct users to sales@verge.io
- Always consider high-availability and data integrity implications in your advice
- Reference verge.io documentation at docs.verge.io when appropriate"""


async def run_support_agent(user_query: str) -> str:
    """Run the verge.io support agent for a single query and return the response."""
    result_text = ""

    async for message in query(
        prompt=user_query,
        options=ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            model="claude-opus-4-6",
            max_turns=5,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_text = block.text

    return result_text


async def interactive_session():
    """Run an interactive support session in the terminal."""
    print("=" * 60)
    print("Welcome to verge.io Technical Support")
    print("Type your question below. Type 'quit' or 'exit' to end.")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye"):
            print("Thank you for contacting verge.io Support. Goodbye!")
            break

        print("\nAgent: ", end="", flush=True)
        response = await run_support_agent(user_input)
        print(response)
        print()


if __name__ == "__main__":
    anyio.run(interactive_session)
