## base llm
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver


from sophy_util import chat

llm = ChatOllama(
    verbose=True,
    model="llama3.2:1b",
    temperature=0.2,
    num_ctx=4096
)

class SophyState(TypedDict):
    exchange: int
    conv_sum: str
    conversation_history: list[AnyMessage]
    latest_exchanges: list[AnyMessage]
    user_input: str

def sophy_chat(chat_state:SophyState):
    exchange = chat_state.get("exchange",0)
    conv_sum = chat_state.get("conv_sum","")
    conversation_history = chat_state.get("conversation_history",[])
    latest_exchanges = chat_state.get("latest_exchanges",[])
    user_input = chat_state["user_input"]
    exchange,conv_sum,conversation_history,latest_exchanges,user_input = chat(llm,exchange,conv_sum,conversation_history,latest_exchanges,user_input, exc_window=5)

    return {
        "exchange":exchange,
        "conv_sum":conv_sum,
        "conversation_history":conversation_history,
        "latest_exchanges":latest_exchanges,
        "user_input":user_input
    }


if __name__ == "__main__":
    builder_ss = StateGraph(SophyState)
    builder_ss.add_node("Sophy",sophy_chat)
    builder_ss.add_edge(START, "Sophy")
    builder_ss.add_edge("Sophy",END)



    memory = MemorySaver()
    sophy_state_graph = builder_ss.compile(
        checkpointer=memory,
    )
    config = {"configurable": {"thread_id": "1"}}

    while True:
        try:
            # Take user input
            user_input = input("You: ")
            events = sophy_state_graph.invoke({"user_input": user_input}, config)
            
            # Check for exit conditions
            if user_input.lower() in ["exit", "quit", "bye", "q"]:
                print("Sophy: Take care! Remember, I'm always here if you need someone to talk to.")
                break
        except Exception as e:
            print(f"Error: {e}")
            pass

    



