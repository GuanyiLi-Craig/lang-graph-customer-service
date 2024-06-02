import shutil
import uuid
import sys

from langchain_core.messages import ToolMessage

from customer_support.config.config import Config
from customer_support.graph import Graph
from customer_support.utils.utils import _print_event

def main():
    try:
        # Let's create an example conversation a user might have with the assistant
        tutorial_questions = [
            "Hi there, what time is my flight?",
            "Am i allowed to update my flight to something sooner? I want to leave later today.",
            "Update my flight to sometime next week then",
            "Update my flight to the earliest one please",
            "The next available option is great",
            "OK cool so it's updated now?",
            "Great - now i want to figure out lodging and transportation?",
            "Yeah i think i'd like an affordable hotel for my week-long stay (7 days)",
            "OK could you place a reservation for your recommended hotel? It sounds nice.",
            "yes go ahead and book anything that's moderate expense and has availability.",
            "Now for a car, what are my options?",
            "Awesome let's just get the cheapest option. Go ahead and book for 7 days",
            "Cool so now what recommendations do you have on excursions?",
            "Are they available while I'm there?",
            "interesting - i like the museums, what options are there? ",
            "OK great pick one and book it for my second day there.",
            "Thank you for your assistant. could you list my whole trip?"
        ]

        # Update with the backup file so we can restart from the original place in each section
        shutil.copy(Config().get_backup_file(), Config().get_db())
        thread_id = str(uuid.uuid4())

        config = {
            "configurable": {
                # The passenger_id is used in our flight tools to
                # fetch the user's flight information
                "passenger_id": "3442 587242",
                # Checkpoints are accessed by thread_id
                "thread_id": thread_id,
            }
        }

        graph = Graph().graph

        graph.get_graph(xray=True).print_ascii()

        _printed = set()
        for question in tutorial_questions:
            events = graph.stream(
                {"messages": ("user", question)}, config, stream_mode="values"
            )
            for event in events:
                _print_event(event, _printed)
            snapshot = graph.get_state(config)
            while snapshot.next:
                # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
                # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
                # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
                user_input = input(
                    "Do you approve of the above actions? Type 'y' to continue;"
                    " otherwise, explain your requested changed.\n\n"
                )
                if user_input.strip() == "y":
                    # Just continue
                    result = graph.invoke(
                        None,
                        config,
                    )
                else:
                    # Satisfy the tool invocation by
                    # providing instructions on the requested changes / change of mind
                    result = graph.invoke(
                        {
                            "messages": [
                                ToolMessage(
                                    tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                                    content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                                )
                            ]
                        },
                        config,
                    )
                snapshot = graph.get_state(config)
    except ValueError as ve:
        return str(ve)

if __name__ == "__main__":
    sys.exit(main())