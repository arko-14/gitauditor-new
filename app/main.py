print("MAIN.PY STARTED")
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from app.github_utils import get_pr_details, post_formal_review
from app.agents_langgraph import run_agent_crew
from app.metrics import metrics_collector
import traceback
import time
import re
import hmac
import os
import sqlite3

app = FastAPI(
    title="Code-Cortex AI Code Reviewer",
    description="Automated PR Review Agent using Groq Llama3 & LangGraph with LangSmith tracing"
)

@app.get("/")
def home():
    return {
        "message": "Code-Cortex AI Agent is Running 🚀",
        "analytics": "/analytics"
    }

@app.get("/analytics")
def get_analytics():
    return metrics_collector.get_stats()

@app.post("/review")
async def review_pr(request: Request):
    try:
        # 1. Parse the Payload
        payload_bytes = await request.body()
        
        # 1a. Webhook Signature Verification
        github_signature = request.headers.get("X-Hub-Signature-256")
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if github_signature and webhook_secret:
            mac = hmac.new(webhook_secret.encode(), msg=payload_bytes, digestmod="sha256")
            expected_sig = "sha256=" + mac.hexdigest()
            if not hmac.compare_digest(expected_sig, github_signature):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
                
        # 1b. Idempotency Key Handling
        delivery_id = request.headers.get("X-GitHub-Delivery")
        db_path = os.getenv("SQLITE_DB_PATH", "events.db")
        if delivery_id:
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS processed_events (delivery_id TEXT PRIMARY KEY)")
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM processed_events WHERE delivery_id = ?", (delivery_id,))
                if cur.fetchone():
                    print(f"Skipping duplicate event: {delivery_id}")
                    return {"status": "Ignored", "message": f"Duplicate delivery ID {delivery_id} skipped."}

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
        start_time = time.time()
        try:
            crew_result = run_agent_crew(diff_text)
            review_result = crew_result["review"]
            tokens = crew_result["tokens"]
        except Exception as e:
            print('Error in run_agent_crew:', e)
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"AI Crew error: {e}")
        
        duration = time.time() - start_time

        import json
        try:
            review_obj = json.loads(review_result)
        except Exception:
            review_obj = {"verdict": "COMMENT", "summary": review_result, "severity": "none", "issues": []}

        # 4. Parse Verdict (Structured JSON)
        action = review_obj.get("verdict", "COMMENT")

        # 5. Extract Severities and Vulnerability Types for Metrics
        severities = {"High": 0, "Medium": 0, "Low": 0}
        vulns = {"SQL Injection": 0, "XSS": 0, "Broken Auth": 0, "Logic Bug": 0}
        
        for issue in review_obj.get("issues", []):
            itype = issue.get("type", "").lower()
            if "sql" in itype: vulns["SQL Injection"] += 1
            elif "xss" in itype or "cross" in itype: vulns["XSS"] += 1
            elif "auth" in itype: vulns["Broken Auth"] += 1
            else: vulns["Logic Bug"] += 1
            
        ov_sev = review_obj.get("severity", "none").lower()
        if ov_sev == "high": severities["High"] = max(1, len(review_obj.get("issues", [])))
        elif ov_sev == "medium": severities["Medium"] = max(1, len(review_obj.get("issues", [])))
        elif ov_sev == "low": severities["Low"] = max(1, len(review_obj.get("issues", [])))

        # Format Markdown for GitHub Comment
        md_lines = [f"**Summary:** {review_obj.get('summary', 'No summary provided.')}\n"]
        if review_obj.get("issues"):
            md_lines.append("### Identified Issues:")
            for idx, issue in enumerate(review_obj["issues"], 1):
                md_lines.append(f"{idx}. **{issue.get('file', 'Unknown')}** ({issue.get('type', 'bug')}):")
                md_lines.append(f"   > {issue.get('reason', '')}")
                if issue.get("fix") and issue.get("fix").strip():
                    md_lines.append(f"   *Suggestion:* \n```\n{issue.get('fix')}\n```")
        formatted_review = "\n".join(md_lines)
        
        # 6. Update Metrics
        metrics_collector.update_metrics(duration, action, severities, tokens, vulns)

        # Record Idempotency
        if delivery_id:
            with sqlite3.connect(db_path) as conn:
                conn.execute("INSERT OR IGNORE INTO processed_events (delivery_id) VALUES (?)", (delivery_id,))

        # 7. Post Result to GitHub
        try:
            post_formal_review(pr_obj, formatted_review, action)
        except Exception as e:
            print('Error posting review:', e)
            traceback.print_exc()
            return {"status": "Partial Success", "verdict": action, "review": review_obj, "error": f"Failed to post review: {e}"}

        return {
            "status": "Success", 
            "verdict": action, 
            "duration_sec": round(duration, 2),
            "review": review_obj
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print('Internal server error:', e)
        traceback.print_exc()
        return {"status": "Error", "error": str(e), "trace": traceback.format_exc()}