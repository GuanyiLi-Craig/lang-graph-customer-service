
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate

from customer_support.utils.utils import get_datetime

class CarBookingAssistantMemory:
    def __init__(self) -> None:
        self.prompt = ChatPromptTemplate.from_messages(
                [
                    (            
                        "system",
                        "You are a specialized assistant for handling car rental bookings. "
                        "The primary assistant delegates work to you whenever the user needs help booking a car rental. "
                        "Search for available car rentals based on the user's preferences and confirm the booking details with the customer. "
                        " When searching, be persistent. Expand your query bounds if the first search returns no results. "
                        "If you need more information or the customer changes their mind, escalate the task back to the main assistant."
                        " Remember that a booking isn't completed until after the relevant tool has successfully been used."
                        "\nCurrent time: {time}."
                        "\n\nIf the user needs help, and none of your tools are appropriate for it, then "
                        '"CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make up invalid tools or functions.'
                        "\n\nSome examples for which you should CompleteOrEscalate:\n"
                        " - 'what's the weather like this time of year?'\n"
                        " - 'What flights are available?'\n"
                        " - 'nevermind i think I'll book separately'\n"
                        " - 'Oh wait i haven't booked my flight yet i'll do that first'\n"
                        " - 'Car rental booking confirmed'",
                    ),
                    ("placeholder", "{messages}"),
                ]
            ).partial(time=get_datetime())