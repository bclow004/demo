"""
VergeOS Support Agent — verge.io infrastructure platform support chatbot.
Uses the Anthropic SDK directly for a clean Q&A chat experience.
"""

import anthropic

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


def run_support_agent(user_query: str, history: list | None = None) -> tuple[str, list]:
    """
    Run the VergeOS support agent for a single query.

    Args:
        user_query: The user's support question.
        history: Prior conversation messages for multi-turn context.

    Returns:
        (response_text, updated_history)
    """
    client = anthropic.Anthropic()

    if history is None:
        history = []

    messages = history + [{"role": "user", "content": user_query}]

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
        thinking={"type": "adaptive"},
    )

    reply = next((b.text for b in response.content if b.type == "text"), "")
    updated_history = messages + [{"role": "assistant", "content": reply}]
    return reply, updated_history


def interactive_session():
    """Run an interactive multi-turn support session in the terminal."""
    print("=" * 60)
    print("  verge.io Technical Support — VergeOS Platform")
    print("  Type 'quit' or 'exit' to end the session.")
    print("=" * 60)
    print()

    history: list = []

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
        reply, history = run_support_agent(user_input, history)
        print(reply)
        print()


if __name__ == "__main__":
    interactive_session()
