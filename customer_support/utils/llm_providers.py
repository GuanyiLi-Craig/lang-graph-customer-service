from langchain_openai import ChatOpenAI
from customer_support.config.config import Config

Config()

ollama_llama3 = ChatOpenAI(
                api_key="ollama",
                model="llama3",
                base_url="http://localhost:11434/v1",
                temperature=0.2
            )

ollama_phi3 = ChatOpenAI(
                api_key="ollama",
                model="phi3",
                base_url="http://localhost:11434/v1",
                temperature=0.2
            )

openai = ChatOpenAI(
                model="gpt-3.5-turbo-0125",
                temperature=0.2
            )

chosen_llm = openai