"""
Verge Support Agent

A customer support agent for Verge built using the Claude Agent SDK.
Handles support inquiries, troubleshooting, and FAQs.
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock

SYSTEM_PROMPT = """You are a knowledgeable and friendly customer support agent for Verge,
a leading technology news and media company covering the intersection of technology, science,
art, and culture.

Your responsibilities include:
- Answering questions about Verge's content, newsletters, podcasts, and video shows
- Helping users with account and subscription issues (e.g., login problems, billing, cancellations)
- Assisting with technical issues on the Verge website or app (e.g., playback, loading errors)
- Providing information about Verge's editorial policies and how to submit tips or corrections
- Guiding users to the right resources (e.g., Verge Science, Decoder podcast, The Vergecast)

Guidelines:
- Be concise, helpful, and empathetic
- If you don't know the answer, say so honestly and suggest contacting support@theverge.com
- Never make up specific account details, pricing, or policies you're unsure about
- For billing or account-specific issues, direct users to theverge.com/account or support@theverge.com
- Keep responses focused on Verge-related topics"""


async def run_support_agent(user_query: str) -> str:
    """Run the Verge support agent for a single query and return the response."""
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
    print("Welcome to Verge Customer Support")
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
            print("Thank you for contacting Verge Support. Goodbye!")
            break

        print("\nAgent: ", end="", flush=True)
        response = await run_support_agent(user_input)
        print(response)
        print()


if __name__ == "__main__":
    anyio.run(interactive_session)
