
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable

from customer_support.agents.agent_abstract import AgentAbstract
from customer_support.agents.hotel_booking.memory import HotelBookingAssistantMemory
from customer_support.agents.hotel_booking.tools import HotelBookingTools

from customer_support.utils.complete_or_escalate import CompleteOrEscalate
from customer_support.utils.llm_providers import chosen_llm


class HotelBookingAssistant(AgentAbstract):
    def __init__(self):
        llm = chosen_llm
        memory = HotelBookingAssistantMemory()
        tools = HotelBookingTools()
        super().__init__(llm, tools, memory, knowledge=None)
    
    def get_runnable(self) -> Runnable:
        return self.memory.prompt | self.llm.bind_tools(
            self.tools.tools + [CompleteOrEscalate]
        )
        


class HotelBookingAssistantInputSchema(BaseModel):
    """Transfer work to a specialized assistant to handle hotel bookings."""

    location: str = Field(
        description="The location where the user wants to book a hotel."
    )
    checkin_date: str = Field(description="The check-in date for the hotel.")
    checkout_date: str = Field(description="The check-out date for the hotel.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the hotel booking."
    )

    class Config:
        schema_extra = {
            "example": {
                "location": "Zurich",
                "checkin_date": "2023-08-15",
                "checkout_date": "2023-08-20",
                "request": "I prefer a hotel near the city center with a room that has a view.",
            }
        }