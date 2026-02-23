# CodeCortex
**Autonomous AI Code Review Agent**

CodeCortex is a backend CI/CD service that autonomously reviews GitHub Pull Requests. It uses a LangGraph state machine and the Groq Llama 3 model to detect logic bugs, security vulnerabilities, and code quality issues, automatically posting verdicts (`APPROVE` or `REQUEST_CHANGES`) directly to the PR.

## 🛠 Tech Stack
- **Backend framework:** FastAPI (Python)
- **Agentic architecture:** LangGraph
- **LLM engine:** Groq (`llama-3.3-70b-versatile`)
- **Git integration:** PyGithub (GitHub App Auth)
- **Deployment:** Docker & Docker Compose

---

## ⚡ Installation & Setup

### 1. The Easy Way (Docker - Recommended)
1. **Clone the repository:**
   ```bash
   git clone https://github.com/arko-14/gitauditor-new.git
   cd gitauditor-new
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```ini
   # Groq API
   GROQ_API_KEY=your_groq_key_here
   
   # GitHub Authentication (Choose ONE)
   # Method 1: GitHub App (Provides higher rate limits)
   GITHUB_APP_ID=your_app_id_here
   GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
   
   # Method 2: Personal Access Token (Fallback method)
   GITHUB_TOKEN=your_github_token_here
   
   # Optional: LangSmith Tracing
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   LANGCHAIN_API_KEY=your_langchain_key
   LANGCHAIN_PROJECT=gitauditor
   ```

3. **Start the Application:**
   ```bash
   docker-compose up --build
   ```

### 2. The Standard Way (Local Python)
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 🔗 Connecting to GitHub Webhooks

To have CodeCortex automatically review Pull Requests:
1. Deploy this application (e.g., using Render, Railway, or Fly.io).
2. Create a **GitHub App** via GitHub Developer Settings.
3. Set the App's **Webhook URL** to `https://your-deployed-app.com/review`.
4. Grant the App **Read & Write** permissions for **Pull Requests** and **Issues**, and **Read-only** for **Contents**.
5. Subscribe the App to **Pull request** events.
6. Install the GitHub App on your target repositories.

### Direct API Testing
You can manually test the local server without triggering a GitHub webhook by using the provided script:
```bash
pip install requests
python test_api.py
```

---

## 🛡️ License

MIT
