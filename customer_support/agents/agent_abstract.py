from abc import ABC, abstractmethod
from dataclasses import dataclass

from langchain_core.runnables import Runnable, RunnableConfig

from customer_support.utils.state import State

@dataclass
class AgentAbstract(ABC):
    llm: object
    tools: object
    memory: object
    knowledge: object
    
    @abstractmethod
    def get_runnable(self) ->  Runnable:
        pass

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.get_runnable().invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}