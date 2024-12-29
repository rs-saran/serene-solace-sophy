from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

def get_char_prompt():
    intro_prompt = '''
    You are Sophy, a mental health assistant who listen and respond with calm, empathy, and understanding.
    REMEMBER: You engage the user as a friend. You do not ask for specifics or for more repeatedly.

    You politely refuse all the requests that are not about discussing their issues.

    You do not offer advice or diagnoses.
    Keep all responses concise and focused solely on the conversation.

    REMEMBER: If the user expresses intent to harm themselves or others, immediately encourage them to call the helpline +9118001234.

    Think step by step about your reply:
    Is your reply brief and to the point?
    Is your reply within context?
    Are you repeatedly asking/suggesting the same thing?

    Returned response should not have more than 50 words
    '''

    return intro_prompt

def get_chat_prompt(conv_summary,latest_exchanges_pretty, exchange, exc_window):
    chat_prompt = ""
    if exchange>=exc_window:
        chat_prompt=f'''
        You must use the below notes and latest exchanges to continue chat

        Latest Exchanges: 
        {latest_exchanges_pretty}

        Previos Exchages Summary:
        {conv_summary}

        '''

    else: 
        chat_prompt=f'''

        You must use the below latest exchanges to continue chat

        Latest Exchanges: 
        {latest_exchanges_pretty}'''

    return chat_prompt

# Functions to summarize the conversation
def summarize_firstk_conversation(llm,firstk_messages):
    
    sum_firstk_template_string = f'''Please make short summarized notes for the therapist bot for reference from the below conversation exchanges. Conversation exchanges: \n\n{firstk_messages} The notes must summarize Human's emotional state, issue, Therapist assistant's conversation direction
    Example Notes:
    Emotional State:
    * Feeling low
    * Recent breakup (implied to be significant)

    Issue:
    * Breakup
    * Painful emotions associated with it

    Therapist Assistant's Conversation Direction:
    * Express empathy and understanding for Rakesh's situation
    * Ask open-ended questions to encourage more information about the breakup and its impact
'''

    summary_response = llm.invoke([("user", sum_firstk_template_string)])

    # print("Summary of first 3 exchannges:\n", summary_response.content)

    return summary_response.content

def summarize_latestk_conversation(llm,conv_sum,latest_exchanges):

    sum_latestk_template_string = f"You are helpful summarizer to a mental health therapy assistant bot. Use the latest exchanges to update the summary notes prepared by the therapist assistant bot. Never include exchanges directly in the notes. The notes must summarize Human's emotional state, issue, Therapist assistant's conversation direction\n\n\n Current notes: \n\n{conv_sum} \n \n\nLatest Exchanges: \n\n{latest_exchanges}"

    summary_response = llm.invoke([("user", sum_latestk_template_string)])

    # print("Summary of latest 3 exchannges:\n", summary_response)

    return summary_response.content

def exchanges_pretty(exchanges, summary=False):
    l = []
    c = "assistant"
    if summary:
        c = "assistant"
    for exc in exchanges:
        if exc.type == 'ai':
            e = f"{c}: {exc.content}"
        else:
            e = f"{exc.type}: {exc.content}"
        l.append(e)
    return "\n".join(l)
    
def chat(llm,exchange,conv_sum,conversation_history,latest_exchanges,user_input, exc_window = 10):
    reset_exchange=-1

    if user_input.lower() in ['exit', 'quit', 'stop', 'q']:
        print("Sophy: Goodbye. Take care.")
        print(end="\n\n\n\n\n")
        print(exchanges_pretty(conversation_history))
    
    if len(conversation_history) <2*exc_window:
        latest_exchanges = conversation_history
    elif exchange%exc_window == 0:
        reset_exchange = exchange
        latest_exchanges_pretty_sum = exchanges_pretty(latest_exchanges,True)
    #     latest_exchanges = conversation_history[-2:]
    # else:
    
    
    latest_exchanges = conversation_history[(2*(reset_exchange-1)):]
    latest_exchanges_pretty = exchanges_pretty(latest_exchanges)
    

    char_prompt = get_char_prompt()

    if exchange == 0:
        sys_prompt = get_char_prompt()
        chat_prompt_msgs = [SystemMessage(char_prompt), HumanMessage(user_input)]
    else:
        if conv_sum=="" and exchange==exc_window:
            # print("Summarizing first k conv. Current Exchange:",exchange)
            conv_sum = summarize_firstk_conversation(llm,latest_exchanges_pretty_sum)
        elif exchange%exc_window == 0:
            # print("Summarizing latest k conv. Current Exchange:",exchange)
            conv_sum = summarize_latestk_conversation(llm,conv_sum,latest_exchanges_pretty_sum)

        sys_prompt = get_chat_prompt(conv_sum, latest_exchanges_pretty, exchange, exc_window)

        chat_prompt_msgs = [SystemMessage(char_prompt), SystemMessage(sys_prompt),SystemMessage("You have identified enough details, Just engage the user in empatheti conversation."), HumanMessage(user_input)]

    exchange+=1

    

    # print("----------------------->")
    # print(exchange)
    # print("You: ", user_input)
    model_response = llm.invoke(chat_prompt_msgs) 

    conversation_history.append(HumanMessage(content=user_input))
    conversation_history.append(AIMessage(content=model_response.content))
    # Print the response
    print(f"Sophy: {model_response.content}")
    # print("<-----------------------")
    # print("\n\n===============================================")

    # print("Prompt Used: ", exchanges_pretty(chat_prompt_msgs))

    # print("\n\n===============================================")
    

    return exchange,conv_sum,conversation_history,latest_exchanges,user_input



if __name__ == "__main__":
    xskip =1