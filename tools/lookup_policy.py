from langchain_core.tools import tool
from services.RAG import RAG
from typing import Dict
import openai
import os


@tool
def lookup_policy(input: str, directory: str, k: int = 1) -> str:
    """Consult the company policies to answer any question related with general
    information or policies of the airline.
    
    Args:
        input: The question to ask
        directory: name of the directory to use
        
    """
    client = openai.OpenAI(api_key= os.getenv("OPENAI_API_KEY"))
    rag = RAG(directory=directory, oai_client=client)   

    info = rag.query(input, k=k)
    return info




