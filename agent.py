from tools.lookup_policy import lookup_policy
from tools.availability import availability
from utils import create_tool_node_with_fallback, _print_event
from services.RAG import RAG
import openai
import os
from state import State
from assistant import Assistant
from datetime import date, datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
import uuid

#Definimos el LLM para el Agent
llm = ChatOpenAI(model="gpt-4o-2024-08-06")


#Definimos el prompt de sistema  para el Agent
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            " You are a helpful customer support assistant for Avior Airlines."
            " Use the provided tools to search for flights, company policies, and other information to assist the user's queries. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "All Fares provided by the tools are total to all the passengeres in the query"
            " If a search comes up empty, as the user for more information to complete the query"
            "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
            "\n\nToday's date is {time}. Use this as the reference point for any date-related questions."
            "The directory to use is  when using lookup_policy is {directory}"
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now().strftime("%A, %d %B %Y, %H:%M"), 
          directory = "./services/faiss_storage" )


# Definimos las herramientas que el agente puede usar
part_1_tools = [
    lookup_policy, 
    availability
]
# Definimos el runnable del agente (LLM + Herramientas)
part_1_assistant_runnable = primary_assistant_prompt | llm.bind_tools(part_1_tools)


#Construimos el grafo del agente
builder = StateGraph(State)


# Definimos nodos del grafo
#Nodo de entrada: Assistant
builder.add_node("assistant", Assistant(part_1_assistant_runnable))
#Nodo de herramientas: create_tool_node_with_fallback
builder.add_node("tools", create_tool_node_with_fallback(part_1_tools))
# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
part_1_graph = builder.compile(checkpointer=memory)

question = 'qUIEN ES EL PRESIDENTE DE AVIOR'
thread_id = str(uuid.uuid4())
current_date = datetime.now().strftime("%A, %d %B %Y")
config = {
    "configurable": {
        
        #the user's name
        "passenger_name": "Juan Carlos",
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
        #Passing the actual date to the model
        "Date": f"Today's date is {current_date}. Use this as the reference point for any date-related questions."
    }
}
_printed = set()
events = part_1_graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
for event in events:
        _print_event(event, _printed)