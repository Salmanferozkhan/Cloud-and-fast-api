"""Main entry point for the Todo Agent."""
import asyncio
import os

from dotenv import load_dotenv,find_dotenv

# Load environment variables BEFORE importing agent (which needs GEMINI_API_KEY)
load_dotenv(find_dotenv())

from agents import Runner

from agent import todo_agent


async def chat_loop():
    """Run an interactive chat loop with the Todo Agent."""
    print("=" * 50)
    print("Todo Agent - Powered by Gemini")
    print("=" * 50)
    print("I can help you manage your todos!")
    print("Commands: Type your request or 'quit' to exit")
    print("=" * 50)
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            # Run the agent
            result = await Runner.run(todo_agent, user_input)
            print(f"\nAgent: {result.final_output}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


async def single_query(query: str):
    """Run a single query against the Todo Agent."""
    result = await Runner.run(todo_agent, query)
    return result.final_output


def main():
    """Main entry point."""
    # Check for Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not set in environment.")
        print("Please set it in .env file or export it:")
        print("  export GEMINI_API_KEY=your-api-key")
        print()

    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
