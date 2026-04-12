import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List, Literal

class Issue(BaseModel):
    type: str = Field(..., description="Vulnerability or bug type (e.g., sql_injection, logic_bug)")
    file: str = Field(..., description="File where the issue was found")
    reason: str = Field(..., description="Explanation of the issue")
    fix: str = Field(..., description="Suggested code fix snippet")

class ManagerVerdict(BaseModel):
    verdict: Literal["APPROVE", "REQUEST_CHANGES"] = Field(..., description="Final verdict on the PR")
    summary: str = Field(..., description="Overall summary of the review")
    severity: Literal["low", "medium", "high", "none"] = Field(..., description="Overall highest severity of issues found")
    issues: List[Issue] = Field(default_factory=list, description="List of issues found in the PR")

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
    ("system", """You are a senior, strict code reviewer. Your sole purpose is to identify logical errors, security vulnerabilities (e.g., SQL injection, XSS), and critical bugs.
You must IGNORE trivial style nitpicks, missing comments, or personal preference formatting.
Analyze the provided unified diff.

Output your review in Markdown. For each issue found, use the following format:
### [Issue Title] (Severity: High/Medium/Low)
**Problem:** [Brief explanation]
**Suggested Fix:** [Code snippet if applicable]

If the code is purely stylistic or safe, state that there are no critical issues.
Always analyze the code changes in the diff below."""),
    ("human", "Here is the unified diff to review:\n\n{diff_text}")
])

manager_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Release Manager. You read the technical review provided by the Senior Reviewer and make the final call on the Pull Request.
If the Senior Reviewer found actual bugs, security risks, or critical logical errors, you must reject the PR.
If the Senior Reviewer only found trivial issues or stated there are no critical issues, you must approve the PR.

Extract all identified issues and provide a structured JSON response using the requested schema."""),
    # Use the actual review output from the reviewer node
    ("human", "Senior Reviewer's analysis:\n\n{review_output}\n\nBased on this analysis, what is your final verdict? Return the parsed evaluation according to the required schema.")
])

# LangGraph state schema using Pydantic BaseModel
class ReviewState(BaseModel):
    diff_text: str
    review_output: str = ""
    final_output: str = ""
    total_tokens: int = 0

# LangGraph nodes
def reviewer_node(state: ReviewState):
    diff_text = state.diff_text
    print("REVIEWER NODE: diff_text received length:", len(diff_text))
    
    # 5. Simple Diff Chunking
    max_chunk_size = 20000
    if len(diff_text) > max_chunk_size:
        chunks = [diff_text[i:i + max_chunk_size] for i in range(0, len(diff_text), max_chunk_size)]
    else:
        chunks = [diff_text]
        
    all_reviews = []
    total_tokens = state.get("total_tokens", 0) if isinstance(state, dict) else state.total_tokens

    for chunk in chunks:
        # Properly format the prompt for chat models
        messages = reviewer_prompt.format_prompt(diff_text=chunk).to_messages()
        response = groq_llm.invoke(messages)
        all_reviews.append(response.content)
        
        # Extract token usage
        usage = response.response_metadata.get("token_usage", {})
        total_tokens += usage.get("total_tokens", 0)
    
    combined_review = "\n\n---\n\n".join(all_reviews)

    # Return full state with updated review_output (as dict)
    if isinstance(state, dict):
        new_state = dict(state)
    else:
        new_state = state.dict()
    new_state["review_output"] = combined_review
    new_state["total_tokens"] = total_tokens
    return new_state

def manager_node(state: ReviewState):
    # Always treat state as dict for safety
    if isinstance(state, dict):
        review_output = state.get("review_output", "")
        new_state = dict(state)
    else:
        review_output = getattr(state, "review_output", "")
        new_state = state.dict()
        
    print("MANAGER NODE: review_output received length:", len(review_output))
    messages = manager_prompt.format_prompt(review_output=review_output).to_messages()
    
    # Structured output binding
    structured_llm = groq_llm.with_structured_output(ManagerVerdict, include_raw=True)
    
    result = structured_llm.invoke(messages)
    
    # Extract structured output and tokens
    import json
    response_metadata = result.get("raw", getattr(result, "raw", None))
    usage = response_metadata.response_metadata.get("token_usage", {}) if hasattr(response_metadata, "response_metadata") else {}
    tokens = usage.get("total_tokens", 0)

    parsed_obj = result.get("parsed")
    
    if parsed_obj:
        if isinstance(parsed_obj, BaseModel):
            final_out_str = parsed_obj.model_dump_json()
        else:
            final_out_str = json.dumps(parsed_obj)
    else:
        # Fallback if structured parsing fails entirely
        final_out_str = json.dumps({"verdict": "COMMENT", "summary": "Failed to parse structured output.", "severity": "none", "issues": []})

    new_state["final_output"] = final_out_str
    new_state["total_tokens"] = new_state.get("total_tokens", 0) + tokens
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
    
    final_out = result.get("final_output", "")
    total_tokens = result.get("total_tokens", 0)

    if not final_out:
        return {
            "review": '{"verdict": "COMMENT", "summary": "Error: Empty output from LLM workflow", "severity": "none", "issues": []}',
            "tokens": total_tokens
        }
        
    return {
        "review": final_out,
        "tokens": total_tokens
    }
