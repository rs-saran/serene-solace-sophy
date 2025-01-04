from sophy_util import chat, company_qna_chat
from dev.graph_util import display_graph
from typing import Union, Literal
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, Graph, START, END
from langgraph.graph import StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_community.vectorstores import FAISS

ss_agent_key = "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"
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=ss_agent_key
)
with open('res\company.md',"r") as f:
    markdown_document = f.read()

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
md_header_splits = markdown_splitter.split_text(markdown_document)
embeddings = OllamaEmbeddings(model="llama3.2:1b")
vectorstore=FAISS.from_documents(md_header_splits, embeddings)
retriever=vectorstore.as_retriever()

class SophyState(TypedDict):
    exchange: int
    conv_sum: str
    conversation_history: list[AnyMessage]
    latest_exchanges: list[AnyMessage]
    user_input: str
    agent_response: str

class AgentResponse(BaseModel):
    "Route to proceed in"
    pickedRoute: str = Field(description= "The route to proceed in, can only be: 'continue_chat', 'crisis_helpline', 'company_qa'")
    reason: str = Field(description ="Reason for picking the route")

llm_agent_response = llm.with_structured_output(AgentResponse)

def sophy_chat(chat_state:SophyState):
    exchange = chat_state.get("exchange",0)
    conv_sum = chat_state.get("conv_sum","")
    conversation_history = chat_state.get("conversation_history",[])
    latest_exchanges = chat_state.get("latest_exchanges",[])
    user_input = chat_state["user_input"]
    # agent_response = chat_state.get("agent_response", None)

    exchange,conv_sum,conversation_history,latest_exchanges,user_input = chat(llm,exchange,conv_sum,conversation_history,latest_exchanges,user_input, exc_window=5)

    return {
        "exchange":exchange,
        "conv_sum":conv_sum,
        "conversation_history":conversation_history,
        "latest_exchanges":latest_exchanges,
        "user_input":user_input
    }



def agent(chat_state:SophyState):

    conversation_history = chat_state.get("conversation_history",[])
    user_input = chat_state["user_input"]

    if len(conversation_history)<2:
        select_conv = conversation_history
    else:
        select_conv = conversation_history[-2:]
    
    prompt = f'''
        You are an autonoums agent in a mental health support chat system.

        Based on the current human input and previous exchanges in the conversation pick the best route for the conversation to proceed in.
        
        Previous Exchanges:
        {select_conv}
        
        Current Human Input:
        {user_input}

        Routes:
        continue_chat : Normal chat route with mental health assistant that assists with common mental health issues like Depression, Anxiety, Stress etc.
        crisis_helpline : Speaclized route connects user to 24X7 crisis helpline to professionals will help the human avoid crisis like suicide.
        company_qa : Specialized route to answer queries about company (serene soalce) information.

        If you can not provide answers for sucidial tendencies or harmful pick the crisis helpine route so that user can recieve help from professionals.

        If undecided and there are no harmful intentions always pick continue_chat

        '''
    
    agent_response  = llm_agent_response.invoke(prompt)

    # print(f"=====> Agent Decision: {agent_response} <=====")
    
    return {"agent_response":agent_response}



def agent_edges(chat_state:SophyState) -> Literal["Sophy", "crisisHandler", "companyQA"]:
    agent_reponse = chat_state.get("agent_response")
    picked_route = agent_reponse.pickedRoute

    if picked_route == 'continue_chat':
        return "Sophy"
    elif picked_route == 'crisis_helpline':
        return "crisisHandler"
    elif picked_route =='company_qa':
        return "companyQA"
    else:
        return "Sophy"

def company_qa(chat_state:SophyState, retriever=retriever): 
    exchange = chat_state.get("exchange",0)
    conv_sum = chat_state.get("conv_sum","")
    conversation_history = chat_state.get("conversation_history",[])
    latest_exchanges = chat_state.get("latest_exchanges",[])
    user_input = chat_state["user_input"]
    print("====> Company QnA <====")

    exchange,conversation_history = company_qna_chat(llm,retriever,conversation_history,user_input, exchange)

    return {
        "exchange":exchange,
        "conv_sum":conv_sum,
        "conversation_history":conversation_history,
        "latest_exchanges":latest_exchanges,
        "user_input":user_input
    }
    

def crisis_handler():
    return "If you are in an active crisis please call 1800-599-0019, a 24/7 toll free helpline launched by the Ministry of Social Justice and Empowerment of India"



if __name__ == "__main__":
    builder = StateGraph(SophyState)
    builder.add_node("Agent",agent)
    builder.add_node("Sophy",sophy_chat)
    builder.add_node("companyQA",company_qa)
    builder.add_node("crisisHandler",crisis_handler)

    builder.add_edge(START, "Agent")
    builder.add_conditional_edges("Agent", agent_edges)
    builder.add_edge("Sophy",END)
    builder.add_edge("companyQA",END)
    builder.add_edge("crisisHandler",END)



    memory = MemorySaver()
    sophy_state_graph = builder.compile(
        checkpointer=memory,
    )
    config = {"configurable": {"thread_id": "1"}}

    

    while True:
        try:
            # Take user input
            user_input = input("You: ")
            # Check for exit conditions
            if user_input.lower() in ["exit", "quit", "bye", "q"]:
                print(
                    "Sophy: Take care! Remember, I'm always here if you need someone to talk to."
                )
                break

            events = sophy_state_graph.invoke({"user_input": user_input}, config)

        except Exception as e:
            print(f"Error: {e}")
            pass
