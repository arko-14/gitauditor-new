import os
from github import Github
from dotenv import load_dotenv
from github import Github, Auth

load_dotenv()

def get_github_client(repo_name: str) -> Github:
    """
    Returns a PyGithub 'Github' instance.
    Checks for GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY first.
    If missing, falls back to GITHUB_TOKEN.
    """
    app_id = os.getenv("GITHUB_APP_ID")
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    if app_id and private_key:
        # 1. Authenticate as the App
        # Ensure private key is properly formatted if passed as single line in env
        private_key = private_key.replace('\\n', '\n')
        app_auth = Auth.AppAuth(app_id, private_key)
        app_gi = Github(auth=app_auth)
        
        # 2. Get the specific installation for this repository
        try:
            parts = repo_name.split('/')
            if len(parts) == 2:
                owner, repo_str = parts[0], parts[1]
                
                # PyGithub requires grabbing the app, then finding the installation for the repo
                app = app_gi.get_app()
                installation = app.get_repo_installation(owner, repo_str)
                
                # 3. Create an installation-specific token
                inst_auth = Auth.AppInstallationAuth(app_auth, installation.id)
                return Github(auth=inst_auth)
            else:
                raise ValueError("Invalid repo_name format. Expected owner/repo")
        except Exception as e:
            import traceback
            print(f"Failed to authenticate via GitHub App for {repo_name}: {e}")
            # Fallback will happen below
    
    # Fallback to Personal Access Token
    token = os.getenv("GITHUB_TOKEN")
    if token:
        print("Using GITHUB_TOKEN for authentication.")
        return Github(token)
    
    raise ValueError("No GitHub authentication credentials found. Set GITHUB_APP_ID/KEY or GITHUB_TOKEN.")

def get_pr_details(repo_name, pr_number):
    print(f'CALLED get_pr_details with repo_name={repo_name}, pr_number={pr_number}')  # Debug print
    try:
        g = get_github_client(repo_name)
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
