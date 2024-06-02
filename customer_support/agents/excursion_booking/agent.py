from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable

from customer_support.agents.agent_abstract import AgentAbstract
from customer_support.agents.excursion_booking.memory import ExcursionBookingAssistantMemory
from customer_support.agents.excursion_booking.tools import ExcursionBookingTools

from customer_support.utils.complete_or_escalate import CompleteOrEscalate
from customer_support.utils.llm_providers import chosen_llm


class ExcursionBookingAssistant(AgentAbstract):
    def __init__(self):
        llm = chosen_llm
        memory = ExcursionBookingAssistantMemory()
        tools = ExcursionBookingTools()
        super().__init__(llm, tools, memory, knowledge=None)

    
    def get_runnable(self) -> Runnable:
        return self.memory.prompt | self.llm.bind_tools(
            self.tools.tools + [CompleteOrEscalate]
        )


class ExcursionBookingAssistantInputSchema(BaseModel):
    """Transfers work to a specialized assistant to handle trip recommendation and other excursion bookings."""

    location: str = Field(
        description="The location where the user wants to book a recommended trip."
    )
    request: str = Field(
        description="Any additional information or requests from the user regarding the trip recommendation."
    )

    class Config:
        schema_extra = {
            "example": {
                "location": "Lucerne",
                "request": "The user is interested in outdoor activities and scenic views.",
            }
        }
