from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable

from customer_support.agents.agent_abstract import AgentAbstract
from customer_support.agents.flight_booking.memory import FlightBookingAssistantMemory
from customer_support.agents.flight_booking.tools import FlightBookingTools

from customer_support.utils.complete_or_escalate import CompleteOrEscalate
from customer_support.utils.llm_providers import chosen_llm

class FlightBookingAssistant(AgentAbstract):
    def __init__(self):
        llm = chosen_llm
        memory = FlightBookingAssistantMemory()
        tools = FlightBookingTools()
        super().__init__(llm, tools, memory, knowledge=None)
     
    def get_runnable(self) -> Runnable:
        return self.memory.prompt | self.llm.bind_tools(
            self.tools.tools + [CompleteOrEscalate]
        )


class FlightBookingAssistantInputSchema(BaseModel):
    """Transfers work to a specialized assistant to handle flight updates and cancellations."""

    request: str = Field(
        description="Any necessary followup questions the update flight assistant should clarify before proceeding."
    )
