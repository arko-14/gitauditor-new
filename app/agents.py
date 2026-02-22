import os
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

print('DEBUG GROQ_API_KEY:', os.getenv('GROQ_API_KEY'))  # Debug print

# LangSmith tracing - comprehensive setup
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "gitauditor")
# LANGCHAIN_API_KEY should be set in .env

# Setup Groq Llama3 model for CrewAI
groq_llm = ChatGroq(
    model="llama3-70b-8192",
    api_key=os.getenv("GROQ_API_KEY")
)

def run_agent_crew(diff_text):
    # Agent 1: The Tech Lead
    reviewer = Agent(
        role='Senior Backend Engineer',
        goal='Analyze code for critical bugs, security flaws, and bad practices.',
        backstory="""You are a strict code reviewer. You hate logical errors, 
        security risks (like SQL injection), and messy code. 
        You focus on the Code Diff provided.""",
        llm=groq_llm,
        verbose=True
    )

    # Agent 2: The Release Manager
    manager = Agent(
        role='Release Manager',
        goal='Decide if the PR should be APPROVED or REQUEST_CHANGES.',
        backstory="""You read the technical review and make the final call. 
        If there are bugs/security issues, you REQUEST_CHANGES. 
        If it is just style nitpicks or clean code, you APPROVE.""",
        llm=groq_llm,
        verbose=True
    )

    # Task 1: Find Bugs
    review_task = Task(
        description=f"Analyze this code diff:\n\n{diff_text}",
        expected_output="A list of technical issues, bugs, and security risks.",
        agent=reviewer
    )

    # Task 2: Final Verdict with Auto-Fix
    decision_task = Task(
        description="""
        Based on the technical review, provide a final decision and FIXED code examples.
        
        YOUR OUTPUT MUST STRICTLY FOLLOW THIS MARKDOWN FORMAT:
        
        VERDICT: [APPROVE or REQUEST_CHANGES]
        
        # Gitauditor Review
        
        ## Summary
        [1-2 sentences explaining the overall quality]
        
        ## Issues & Fixes
        
        ### 1. [Issue Title] (Severity: High/Medium/Low)
        **Problem:** [Explanation of the bug]
        **Suggested Fix:**
        ```python
        # Write the CORRECTED code here
        def secure_function():
            # Logic without the bug
            ...
        ```
        
        *(Repeat for other issues. If no issues, say "Code looks clean! ")*
        """,
        expected_output="Markdown formatted review with code fixes.",
        agent=manager,
        context=[review_task]
    )

    crew = Crew(
        agents=[reviewer, manager],
        tasks=[review_task, decision_task],
        process=Process.sequential
    )

    result = crew.kickoff()
    return str(result)
