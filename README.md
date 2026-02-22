# Git Auditor

**Autonomous Multi-Agent Code Reviewer**

**Gitauditor** is an intelligent CI/CD agent that autonomously reviews GitHub Pull Requests. It uses a **LangGraph** architecture and the **Groq Llama 3** model to "think" like a human engineering team, detecting logic bugs, security flaws, and style issues before they merge.

## 🚀 Features

* **🤖 AI Agent Orchestration (LangGraph)**
    * **Senior Reviewer Node:** Deep dives into code diffs to find SQL injections, hardcoded secrets, and logic flaws.
    * **Release Manager Node:** Aggregates findings and formats them into a crisp, actionable Markdown review (`APPROVE` vs `REQUEST_CHANGES`).
* **⚡ Auto-Fix Suggestions:** Provides ready-to-copy code fixes directly in the GitHub comments.
* **🚀 Blazing Fast Inference:** Powered by **Groq (`llama-3.3-70b-versatile`)** for incredibly fast inference latency.
* **� Docker Ready:** Instantly spin up the API using Docker Compose.

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[GitHub Webhook / POST /review] --> B(FastAPI Gateway)
    B --> C{LangGraph StateMachine}
    C -->|Analyze Diff| D[🕵️‍♂️ Senior Reviewer Node]
    C -->|Format Verdict| E[⚖️ Release Node]
    D <-->|LLM Inference| F[Groq API (Llama 3)]
    E <-->|LLM Inference| F
    E -->|JSON Result| B
    B -->|Post Comment| G[GitHub API]
```

---

## 🛠️ Tech Stack

* **Backend Framework:** FastAPI (Python)
* **Agentic Framework:** LangGraph
* **LLM Engine:** Groq (Llama 3 70B)
* **Git Integration:** PyGithub
* **Containerization:** Docker & Docker Compose

---

## ⚡ Installation & Setup

### 🐳 The Easy Way (Docker - Recommended)

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
   
   # GitHub Token (Requires 'repo' scope)
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

### 🐍 The Standard Way (Local Python)

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 🎮 Usage

### Direct API Testing
You can easily test the running agent using the provided test script:
```bash
pip install requests
python test_api.py
```

Or via cURL:
```bash
curl -X POST http://localhost:8000/review \
     -H "Content-Type: application/json" \
     -d '{"github_url": "https://github.com/arko-14/gitauditor/pull/3"}'
```

### 🔗 Connecting to GitHub Webhooks
To have Gitauditor review Pull Requests instantly when they are opened on any repository:
1. Deploy your FastAPI application to a host like Render, Railway, or Fly.io.
2. Go to the Repository Settings of the repo you want to audit -> **Webhooks**.
3. Add a webhook pointing to `https://your-deployed-app.com/review`.
4. Ensure the Content type is `application/json`.
5. Ensure the GitHub account holding the `GITHUB_TOKEN` is added as a collaborator to the target repository.

---

## 🛡️ License

MIT
