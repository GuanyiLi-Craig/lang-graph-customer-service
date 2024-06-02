from typing import Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from langchain_core.messages import ToolMessage

from customer_support.agents.car_booking.agent import CarBookingAssistant, CarBookingAssistantInputSchema
from customer_support.agents.excursion_booking.agent import ExcursionBookingAssistant, ExcursionBookingAssistantInputSchema
from customer_support.agents.flight_booking.agent import FlightBookingAssistant, FlightBookingAssistantInputSchema
from customer_support.agents.hotel_booking.agent import HotelBookingAssistant, HotelBookingAssistantInputSchema
from customer_support.agents.primary_assistant.agent import PrimaryAssistant

from customer_support.agents.flight_booking.tools import FlightBookingTools

from customer_support.utils.complete_or_escalate import CompleteOrEscalate
from customer_support.utils.state import State
from customer_support.utils.utils import create_tool_node_with_fallback, create_entry_node


class Graph:
    def __init__(self) -> None:
        self.builder = StateGraph(State)
        self.init_builder()
        self.add_flight_booking_assistant()
        self.add_leaving_skill()
        self.add_car_booking_assistant()
        self.add_hotel_booking_assistant()
        self.add_excursion_booking_assistant()
        self.add_primary_assistant()

        self.builder.add_conditional_edges("fetch_user_info", self.route_to_workflow)

        self.graph = self.builder.compile(
            checkpointer=SqliteSaver.from_conn_string(":memory:"),
            # Let the user approve or deny the use of sensitive tools
            interrupt_before=[
                "flight_booking_sensitive_tools",
                "car_booking_sensitive_tools",
                "hotel_booking_sensitive_tools",
                "excursion_booking_sensitive_tools",
            ],
        )

    def user_info(self, state: State):
        return {"user_info": FlightBookingTools().fetch_user_flight_information.invoke({})}
    
    def route_to_workflow(self, state: State, ) -> Literal[
            "primary_assistant",
            "flight_booking",
            "car_booking",
            "hotel_booking",
            "excursion_booking",
        ]:
        """If we are in a delegated state, route directly to the appropriate assistant."""
        dialog_state = state.get("dialog_state")
        if not dialog_state:
            return "primary_assistant"
        return dialog_state[-1]



    def init_builder(self):
        self.builder.add_node("fetch_user_info", self.user_info)
        self.builder.set_entry_point("fetch_user_info")

    
    def add_flight_booking_assistant(self):

        flight_booking_assistant  = FlightBookingAssistant()

        def route_flight_booking(state: State) -> Literal[
            "flight_booking_sensitive_tools",
            "flight_booking_safe_tools",
            "leave_skill",
            "__end__",
        ]:
            route = tools_condition(state)
            if route == END:
                return END
            tool_calls = state["messages"][-1].tool_calls
            did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
            if did_cancel:
                return "leave_skill"
            safe_toolnames = [t.name for t in flight_booking_assistant.tools.safe_tools]
            if all(tc["name"] in safe_toolnames for tc in tool_calls):
                return "flight_booking_safe_tools"
            return "flight_booking_sensitive_tools"


        # flight booking assistant
        self.builder.add_node(
            "enter_flight_booking",
            create_entry_node("Flight Updates & Booking Assistant", "flight_booking"),
        )
        self.builder.add_node("flight_booking", flight_booking_assistant)
        self.builder.add_edge("enter_flight_booking", "flight_booking")
        self.builder.add_node(
            "flight_booking_sensitive_tools",
            create_tool_node_with_fallback(flight_booking_assistant.tools.sensitive_tools),
        )
        self.builder.add_node(
            "flight_booking_safe_tools",
            create_tool_node_with_fallback(flight_booking_assistant.tools.safe_tools),
        )
        self.builder.add_edge("flight_booking_sensitive_tools", "flight_booking")
        self.builder.add_edge("flight_booking_safe_tools", "flight_booking")
        self.builder.add_conditional_edges("flight_booking", route_flight_booking)


    def add_leaving_skill(self):

        def pop_dialog_state(state: State) -> dict:
            """Pop the dialog stack and return to the main assistant.

            This lets the full graph explicitly track the dialog flow and delegate control
            to specific sub-graphs.
            """
            messages = []
            if state["messages"][-1].tool_calls:
                # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
                messages.append(
                    ToolMessage(
                        content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                        tool_call_id=state["messages"][-1].tool_calls[0]["id"],
                    )
                )
            return {
                "dialog_state": "pop",
                "messages": messages,
            }


        self.builder.add_node("leave_skill", pop_dialog_state)
        self.builder.add_edge("leave_skill", "primary_assistant")

    
    def add_car_booking_assistant(self):

        car_booking_assistant = CarBookingAssistant()

        def route_car_booking(
            state: State,
        ) -> Literal[
            "car_booking_safe_tools",
            "car_booking_sensitive_tools",
            "leave_skill",
            "__end__",
        ]:
            route = tools_condition(state)
            if route == END:
                return END
            tool_calls = state["messages"][-1].tool_calls
            did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
            if did_cancel:
                return "leave_skill"
            safe_toolnames = [t.name for t in car_booking_assistant.tools.safe_tools]
            if all(tc["name"] in safe_toolnames for tc in tool_calls):
                return "car_booking_safe_tools"
            return "car_booking_sensitive_tools"

        self.builder.add_node(
            "enter_car_booking",
            create_entry_node("Car Rental Assistant", "car_booking"),
        )
        self.builder.add_node("car_booking", car_booking_assistant)
        self.builder.add_edge("enter_car_booking", "car_booking")
        self.builder.add_node(
            "car_booking_safe_tools",
            create_tool_node_with_fallback(car_booking_assistant.tools.safe_tools),
        )
        self.builder.add_node(
            "car_booking_sensitive_tools",
            create_tool_node_with_fallback(car_booking_assistant.tools.sensitive_tools),
        )

        self.builder.add_edge("car_booking_sensitive_tools", "car_booking")
        self.builder.add_edge("car_booking_safe_tools", "car_booking")
        self.builder.add_conditional_edges("car_booking", route_car_booking)


    def add_hotel_booking_assistant(self):

        hotel_booking_assistant = HotelBookingAssistant()

        def route_hotel_booking(
            state: State,
        ) -> Literal[
            "leave_skill", "hotel_booking_safe_tools", "hotel_booking_sensitive_tools", "__end__"
        ]:
            route = tools_condition(state)
            if route == END:
                return END
            tool_calls = state["messages"][-1].tool_calls
            did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
            if did_cancel:
                return "leave_skill"
            tool_names = [t.name for t in hotel_booking_assistant.tools.safe_tools]
            if all(tc["name"] in tool_names for tc in tool_calls):
                return "hotel_booking_safe_tools"
            return "hotel_booking_sensitive_tools"
        
        self.builder.add_node(
            "enter_hotel_booking", create_entry_node("Hotel Booking Assistant", "hotel_booking")
        )
        self.builder.add_node("hotel_booking", hotel_booking_assistant)
        self.builder.add_edge("enter_hotel_booking", "hotel_booking")
        self.builder.add_node(
            "hotel_booking_safe_tools",
            create_tool_node_with_fallback(hotel_booking_assistant.tools.safe_tools),
        )
        self.builder.add_node(
            "hotel_booking_sensitive_tools",
            create_tool_node_with_fallback(hotel_booking_assistant.tools.sensitive_tools),
        )
        self.builder.add_edge("hotel_booking_sensitive_tools", "hotel_booking")
        self.builder.add_edge("hotel_booking_safe_tools", "hotel_booking")
        self.builder.add_conditional_edges("hotel_booking", route_hotel_booking)


    def add_excursion_booking_assistant(self):

        excursion_booking_assistant = ExcursionBookingAssistant()

        def route_excursion_booking(
            state: State,
        ) -> Literal[
            "excursion_booking_safe_tools",
            "excursion_booking_sensitive_tools",
            "leave_skill",
            "__end__",
        ]:
            route = tools_condition(state)
            if route == END:
                return END
            tool_calls = state["messages"][-1].tool_calls
            did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
            if did_cancel:
                return "leave_skill"
            tool_names = [t.name for t in excursion_booking_assistant.tools.safe_tools]
            if all(tc["name"] in tool_names for tc in tool_calls):
                return "excursion_booking_safe_tools"
            return "excursion_booking_sensitive_tools"

        self.builder.add_node(
            "enter_excursion_booking",
            create_entry_node("Trip Recommendation Assistant", "excursion_booking"),
        )
        self.builder.add_node("excursion_booking", excursion_booking_assistant)
        self.builder.add_edge("enter_excursion_booking", "excursion_booking")
        self.builder.add_node(
            "excursion_booking_safe_tools",
            create_tool_node_with_fallback(excursion_booking_assistant.tools.safe_tools),
        )
        self.builder.add_node(
            "excursion_booking_sensitive_tools",
            create_tool_node_with_fallback(excursion_booking_assistant.tools.sensitive_tools),
        )

        self.builder.add_edge("excursion_booking_sensitive_tools", "excursion_booking")
        self.builder.add_edge("excursion_booking_safe_tools", "excursion_booking")
        self.builder.add_conditional_edges("excursion_booking", route_excursion_booking)


    def add_primary_assistant(self):

        primary_assistant = PrimaryAssistant()

        def route_primary_assistant(
            state: State,
        ) -> Literal[
            "primary_assistant_tools",
            "enter_flight_booking",
            "enter_hotel_booking",
            "enter_excursion_booking",
            "__end__",
        ]:
            route = tools_condition(state)
            if route == END:
                return END
            tool_calls = state["messages"][-1].tool_calls
            if tool_calls:
                if tool_calls[0]["name"] == FlightBookingAssistantInputSchema.__name__:
                    return "enter_flight_booking"
                elif tool_calls[0]["name"] == CarBookingAssistantInputSchema.__name__:
                    return "enter_car_booking"
                elif tool_calls[0]["name"] == HotelBookingAssistantInputSchema.__name__:
                    return "enter_hotel_booking"
                elif tool_calls[0]["name"] == ExcursionBookingAssistantInputSchema.__name__:
                    return "enter_excursion_booking"
                return "primary_assistant_tools"
            raise ValueError("Invalid route")
        
        self.builder.add_node("primary_assistant", primary_assistant)
        self.builder.add_node(
            "primary_assistant_tools", create_tool_node_with_fallback(primary_assistant.tools)
        )

        self.builder.add_conditional_edges(
            "primary_assistant",
            route_primary_assistant,
            {
                "enter_flight_booking": "enter_flight_booking",
                "enter_car_booking": "enter_car_booking",
                "enter_hotel_booking": "enter_hotel_booking",
                "enter_excursion_booking": "enter_excursion_booking",
                "primary_assistant_tools": "primary_assistant_tools",
                END: END,
            },
        )
        self.builder.add_edge("primary_assistant_tools", "primary_assistant")