import warnings
warnings.filterwarnings("ignore")
import langchain
from langchain_openai import ChatOpenAI
import os 
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph,END
from typing import TypedDict,Annotated,List
import operator
from langchain_core.messages import AnyMessage,SystemMessage,HumanMessage,AIMessage,ChatMessage
from langgraph.checkpoint.sqlite import SqliteSaver
memory= SqliteSaver.from_conn_string(":memory:").__enter__()



tool=TavilySearchResults(max_reults=2,tavily_api_key="add your key")
os.environ["OPENAI_API_KEY"]="add your key"


class AgentState(TypedDict):
    task: str
    plan: str
    draft :str
    critique: str
    content: List[str]
    revision_num: int
    max_revision: int

model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)


PLAN_PROMPT = """You are an expert writer tasked with writing a high level outline of an essay. \
Write such an outline for the user provided topic. Give an outline of the essay along with any relevant notes \
or instructions for the sections."""

WRITER_PROMPT = """You are an essay assistant tasked with writing excellent 5-paragraph essays.\
Generate the best essay possible for the user's request and the initial outline. \
If the user provides critique, respond with a revised version of your previous attempts. \
Utilize all the information below as needed: 

------

{content}"""

REFLECTION_PROMPT = """You are a teacher grading an essay submission. \
Generate critique and recommendations for the user's submission. \
Provide detailed recommendations, including requests for length, depth, style, etc."""

RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can \
be used when writing the following essay. Generate a list of search queries that will gather \
any relevant information. Only generate 3 queries max."""

RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can \
be used when making any requested revisions (as outlined below). \
Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""

#from langchain_core.pydantic_v1 import BaseModel
from pydantic import BaseModel
class Quaries(BaseModel):
    queries: List[str]

def plan_node(state: AgentState):
    message=[SystemMessage(content=PLAN_PROMPT),
             HumanMessage(content=state["task"])]
    response=model.invoke(message)
    return {"plan":response.content}

def research_plan_node(state:AgentState):
    queries=model.with_structured_output(Quaries).invoke([
        SystemMessage(content=RESEARCH_PLAN_PROMPT),
        HumanMessage(content=state["task"])
    ])
    content= state['content'] or []
    for q in queries.queries:
        response= tool({"query":q})
        for r in response:
            if isinstance(r, dict):
                text = r.get("content")
                if isinstance(text, str):
                    content.append(text[:1000])
    return {"content":content}

def clean_content(raw_content, max_items=5, max_chars_per_item=1000):

    clean = []
    for item in raw_content[:max_items]:
        if isinstance(item, dict):
            text = item.get("content") or item.get("title") or ""
        elif isinstance(item, str):
            text = item
        else:
            continue
        clean.append(text.strip()[:max_chars_per_item])
    return clean

def generate_node(state:AgentState):
    content = clean_content(state["content"])
    #content="\n\n".join(state["content"] or [])
    user_message=HumanMessage(content=f"{state['task']}\n\n Here is my plan: \n\n {state['plan']}")
    message=[SystemMessage(content=WRITER_PROMPT.format(content=content)),
             user_message]
    response=model.invoke(message)
    return {"draft": response.content,"revision_num":state.get("revision_num",1)+1}

def refection_node(State:AgentState):
    message=[SystemMessage(content=REFLECTION_PROMPT),
             HumanMessage(content=State["draft"])
             ]
    response= model.invoke(message)
    return {"critique":response.content}

def research_critique_node(state:AgentState):
    queries=model.with_structured_output(Quaries).invoke([
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state["critique"])
    ])
    content=state["content"] or []
    for q in queries.queries:
        response=tool({"query":q})
        for r in response:
            if isinstance(r, dict):
                text = r.get("content")
                if isinstance(text, str):
                    content.append(text[:1000])
    return {"content":content}

def should_continue(state):
    if state["revision_num"]> state["max_revision"]:
        return END
    return "reflect"

builder=StateGraph(AgentState)

builder.add_node("planner",plan_node)
builder.add_node("generate",generate_node)
builder.add_node("reflect",refection_node)
builder.add_node("research_plan",research_plan_node)
builder.add_node("research_critique",research_critique_node)

builder.set_entry_point("planner")
 
builder.add_conditional_edges("generate",should_continue,{END:END,"reflect":"reflect"})

builder.add_edge("planner","research_plan")
builder.add_edge("research_plan","generate")
builder.add_edge("reflect","research_critique")
builder.add_edge("research_critique","generate")


#graph=builder.compile(checkpointer=memory)



# thread = {"configurable": {"thread_id": "1"}}
# for s in graph.stream({
#     'task': "what is the difference between langchain and langsmith",
#     "max_revisions": 2,
#     "revision_number": 1,
# }, thread):
#     print(s)

from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string(":memory:") as memory:
    graph = builder.compile(checkpointer=memory)

    input_data = {
        'task': "what is the difference between langchain and langsmith",
        "max_revision": 2,
        "revision_num": 1,
        "content": [],         
    "plan": "",           
    "draft": "",           
    "critique": "",   
    }

    thread = {"configurable": {"thread_id": "1"}}

    for s in graph.stream(input_data, thread):
        print(s)
