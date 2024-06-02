from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable

from customer_support.agents.agent_abstract import AgentAbstract
from customer_support.agents.car_booking.memory import CarBookingAssistantMemory
from customer_support.agents.car_booking.tools import CarBookingTools

from customer_support.utils.complete_or_escalate import CompleteOrEscalate
from customer_support.utils.llm_providers import chosen_llm


class CarBookingAssistant(AgentAbstract):
    def __init__(self):
        llm = chosen_llm
        tools = CarBookingTools()
        memory = CarBookingAssistantMemory()
        super().__init__(llm, tools, memory, knowledge=None)

    def get_runnable(self) -> Runnable:
        return self.memory.prompt | self.llm.bind_tools(
            self.tools.tools + [CompleteOrEscalate]
        )
        

class CarBookingAssistantInputSchema(BaseModel):
    """Transfers work to a specialized assistant to handle car rental bookings."""

    location: str = Field(
        description="The location where the user wants to rent a car."
    )
    start_date: str = Field(description="The start date of the car rental.")
    end_date: str = Field(description="The end date of the car rental.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the car rental."
    )

    class Config:
        schema_extra = {
            "example": {
                "location": "Basel",
                "start_date": "2023-07-01",
                "end_date": "2023-07-05",
                "request": "I need a compact car with automatic transmission.",
            }
        }
