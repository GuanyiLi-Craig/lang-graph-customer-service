from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import Runnable

from customer_support.agents.agent_abstract import AgentAbstract

from customer_support.agents.car_booking.agent import CarBookingAssistantInputSchema
from customer_support.agents.excursion_booking.agent import ExcursionBookingAssistantInputSchema
from customer_support.agents.flight_booking.agent import FlightBookingAssistantInputSchema
from customer_support.agents.flight_booking.tools import FlightBookingTools
from customer_support.agents.hotel_booking.agent import HotelBookingAssistantInputSchema

from customer_support.agents.primary_assistant.memory import PrimaryAssistantMemory
from customer_support.agents.primary_assistant.tools import PrimaryAssistantTools

from customer_support.utils.llm_providers import chosen_llm


class PrimaryAssistant(AgentAbstract):
    def __init__(self):
        llm = chosen_llm
        tools = [
            TavilySearchResults(max_results=1),
            FlightBookingTools().search_flights,
            PrimaryAssistantTools().lookup_policy,
        ]
        memory = PrimaryAssistantMemory()
        super().__init__(llm, tools, memory, knowledge=None)
    
    def get_runnable(self) -> Runnable:
        return self.memory.prompt | self.llm.bind_tools(self.tools + [
            CarBookingAssistantInputSchema,
            ExcursionBookingAssistantInputSchema,
            FlightBookingAssistantInputSchema,
            HotelBookingAssistantInputSchema,
        ])
