print("MAIN.PY STARTED")
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from app.github_utils import get_pr_details, post_formal_review
from app.agents_langgraph import run_agent_crew  # Use LangGraph+Groq implementation
import traceback  # Add this for error logging

app = FastAPI(
    title="Gitauditor Code Reviewer",
    description="Automated PR Review Agent using Groq Llama3 & LangGraph with LangSmith tracing"
)

@app.get("/")
def home():
    return {"message": "Gitauditor Agent is Running 🚀"}

@app.post("/review")
async def review_pr(request: Request):
    try:
        # 1. Parse the Payload
        payload = await request.json()
        
        repo_name = None
        pr_number = None

        # Handle direct test scripts (Old method)
        if "github_url" in payload:
            try:
                parts = payload["github_url"].split("github.com/")[-1].split("/")
                repo_name = f"{parts[0]}/{parts[1]}"
                pr_number = int(parts[3])
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid GitHub Pull Request URL.")
        
        # Handle ACTUAL GitHub Webhooks
        elif "pull_request" in payload and "repository" in payload:
            # We only want to review when PRs are opened or synchronized (updated)
            action = payload.get("action")
            if action not in ["opened", "synchronize", "reopened"]:
                return {"status": "Ignored", "message": f"Action '{action}' is not reviewable."}
            
            repo_name = payload["repository"]["full_name"]
            pr_number = payload["pull_request"]["number"]
            
        else:
            raise HTTPException(status_code=400, detail="Invalid payload format. Expected 'github_url' or GitHub PR Webhook.")

        print(f"🔍 Analyzing PR: {repo_name} #{pr_number}")

        # 2. Fetch Code
        pr_obj, diff_text = get_pr_details(repo_name, pr_number)
        
        if not pr_obj:
            raise HTTPException(status_code=404, detail="Repo not found or error fetching PR.")
        
        if not diff_text:
            return {"status": "Skipped", "message": "No code changes found in this PR."}

        # 3. Run AI Crew (now LangGraph)
        print("🤖 AI Crew (LangGraph) starting...")
        try:
            review_result = run_agent_crew(diff_text)
        except Exception as e:
            print('Error in run_agent_crew:', e)
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"AI Crew error: {e}")
        
        # 4. Parse Verdict (Simple Logic)
        action = "COMMENT"
        if "VERDICT: APPROVE" in review_result:
            action = "APPROVE"
        elif "VERDICT: REQUEST_CHANGES" in review_result:
            action = "REQUEST_CHANGES"

        # 5. Post Result to GitHub
        try:
            post_formal_review(pr_obj, review_result, action)
        except Exception as e:
            print('Error posting review:', e)
            traceback.print_exc()
            return {"status": "Partial Success", "verdict": action, "review": review_result, "error": f"Failed to post review: {e}"}

        return {
            "status": "Success", 
            "verdict": action, 
            "review": review_result
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print('Internal server error:', e)
        traceback.print_exc()
        return {"status": "Error", "error": str(e), "trace": traceback.format_exc()}