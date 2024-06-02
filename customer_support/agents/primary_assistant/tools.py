
from langchain_core.tools import tool

from customer_support.agents.primary_assistant.knowledge import PrimaryAssistantKnowledge

knowledge = PrimaryAssistantKnowledge()

class PrimaryAssistantTools:

    @tool
    def lookup_policy(query: str) -> str:
        """Consult the company policies to check whether certain options are permitted.
        Use this before making any flight changes performing other 'write' events."""
        docs = knowledge.retriever.query(query, k=2)
        return "\n\n".join([doc["page_content"] for doc in docs])