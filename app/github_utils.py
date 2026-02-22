import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

# Initialize GitHub
g = Github(os.getenv("GITHUB_TOKEN"))

def get_pr_details(repo_name, pr_number):
    print(f'CALLED get_pr_details with repo_name={repo_name}, pr_number={pr_number}')  # Debug print
    try:
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        print(f'Fetched PR: {pr}')  # Debug print
        files = list(pr.get_files()[:5])
        print(f'PR files: {[f.filename for f in files]}')  # Debug print
        diff_text = ""
        for file in files:
            if file.status != "removed":
                diff_text += f"{file.patch}\n\n"
        print('DEBUG DIFF_TEXT:', diff_text)  # Debug print
        return pr, diff_text
    except Exception as e:
        print(f"Error fetching PR: {e}")
        return None, None

def post_formal_review(pr, review_content, action="COMMENT"):
    """
    Tries to post a Formal Review. 
    If that fails (due to permissions or self-review rules), 
    falls back to a regular comment.
    """
    try:
        
            # Attempt 2: Fallback (Regular Comment)
            # This ALWAYS works, even on your own PR
        formatted_body = f"## 🤖 Automated Review Verdict: {action}\n\n{review_content}"
        pr.create_issue_comment(formatted_body)
        print(f"✅ Posted COMMENT to PR #{pr.number}")
        return True
    except Exception as e2:
            print(f"Critical Error: Could not post comment either: {e2}")
            return False
