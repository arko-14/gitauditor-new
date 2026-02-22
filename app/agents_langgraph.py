import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "gitauditor")

# LLM setup
groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Prompts
reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a strict code reviewer. You hate logical errors, security risks (like SQL injection), and messy code. You focus on the unified diff provided. Always analyze the code changes in the diff below."),
    ("human", "Here is the unified diff to review:\n\n{diff_text}")
])

manager_prompt = ChatPromptTemplate.from_messages([
    ("system", "You read the technical review and make the final call. If there are bugs/security issues, you REQUEST_CHANGES. If it is just style nitpicks or clean code, you APPROVE."),
    # Use the actual review output from the reviewer node
    ("human", "{review_output}")
])

# LangGraph state schema using Pydantic BaseModel
class ReviewState(BaseModel):
    diff_text: str
    review_output: str = ""
    final_output: str = ""

# LangGraph nodes
def reviewer_node(state: ReviewState):
    diff_text = state.diff_text
    print("REVIEWER NODE: diff_text received:", diff_text)
    # Properly format the prompt for chat models
    messages = reviewer_prompt.format_prompt(diff_text=diff_text).to_messages()
    print("REVIEWER NODE: messages sent to LLM:", messages)
    response = groq_llm.invoke(messages)
    print("REVIEWER NODE: LLM response:", response.content)
    # Return full state with updated review_output (as dict)
    if isinstance(state, dict):
        new_state = dict(state)
    else:
        new_state = state.dict()
    new_state["review_output"] = response.content
    return new_state

def manager_node(state: ReviewState):
    # Always treat state as dict for safety
    if isinstance(state, dict):
        review_output = state.get("review_output", "")
        new_state = dict(state)
    else:
        review_output = getattr(state, "review_output", "")
        new_state = state.dict()
    print("MANAGER NODE: review_output received:", review_output)
    messages = manager_prompt.format_prompt(review_output=review_output).to_messages()
    print("MANAGER NODE: messages sent to LLM:", messages)
    response = groq_llm.invoke(messages)
    print("MANAGER NODE: LLM response:", response.content)
    new_state["final_output"] = response.content
    return new_state

# Build the graph
graph = StateGraph(ReviewState)
graph.add_node("reviewer", reviewer_node)
graph.add_node("manager", manager_node)
graph.add_edge("reviewer", "manager")
graph.add_edge("manager", END)
graph.set_entry_point("reviewer")

langgraph_workflow = graph.compile()

def run_agent_crew(diff_text):
    state = ReviewState(diff_text=diff_text)
    result = langgraph_workflow.invoke(state)
    # Defensive: If the review_output is missing, return a clear error
    if not result.get("final_output") or "{review_output}" in result.get("final_output", ""):
        return "ERROR: The technical review output was not passed correctly. Please check the workflow logic."
    return result["final_output"]
