


# Git Auditor

 Autonomous Multi-Agent Code Reviewer

**Gitauditor** is an intelligent CI/CD agent that autonomously reviews GitHub Pull Requests. Unlike standard static analysis tools, it uses a **Multi-Agent Architecture (CrewAI)** to "think" like a human engineering team, detecting logic bugs, security flaws, and style issues before they merge.


## 🚀 Features

* **🤖 Multi-Agent Orchestration**
    * **Senior Reviewer Agent:** Deep dives into code diffs to find SQL injections, hardcoded secrets, and infinite loops.
    * **Release Manager Agent:** Aggregates findings and issues a formal verdict (`APPROVE` vs `REQUEST_CHANGES`).
* **⚡ Auto-Fix Suggestions:** Doesn't just complain—provides ready-to-copy code fixes for detected bugs directly in the GitHub comments.
* **🚀 Inference:** Optimized for **Gemini 2.5 Pro** for inference latency and massive context windows.
* **🔗 Formal GitHub Integration:** Connects directly to the GitHub API to block merges on critical issues using formal PR reviews.



## 🏗️ System Architecture

```mermaid
graph TD
    A[User/Webhook] -->|POST /review| B(FastAPI Gateway)
    B --> C{CrewAI Orchestrator}
    C -->|Task 1: Analyze Diff| D[🕵️‍♂️ Senior Reviewer Agent]
    C -->|Task 2: Final Verdict| E[⚖️ Release Manager Agent]
    D <-->|LLM Inference| F[Gemini API]
    E <-->|LLM Inference| F
    E -->|JSON Verdict| B
    B -->|POST Review| G[GitHub API]
````

-----

## 🛠️ Tech Stack

  * **Backend Framework:** FastAPI (Python)
  * **Orchestration:** CrewAI (Agentic Workflows)
  * **LLM Engine:** Google Gemini 2.5 Flash 
  * **Git Integration:** PyGithub

-----

## ⚡ Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/your-username/gitauditor.git](https://github.com/your-username/gitauditor.git)
    cd gitauditor
    ```

2.  **Install Dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    Create a `.env` file in the root directory:

    ```ini
    # LLM Provider (Groq or Google)
    GROQ_API_KEY=gsk_...
    # GOOGLE_API_KEY=AIza...

    # GitHub Token (Must have 'repo' scope)
    GITHUB_TOKEN=ghp_...
    ```

4.  **Run the Agent:**

    ```bash
    uvicorn app.main:app --reload
    ```

-----

## 🎮 Usage

### Triggering a Review (Manual Mode)

For this prototype, the agent exposes a REST endpoint for easy testing and demonstration.

1.  Start the server and navigate to the Swagger UI: `http://127.0.0.1:8000/docs`
2.  Use the **POST /review** endpoint.
3.  Payload:
    ```json
    {
      "github_url": "[https://github.com/your-username/your-repo/pull/1](https://github.com/your-username/your-repo/pull/1)"
    }
    ```
4.  **Result:** The agent will analyze the PR diff, print the multi-agent reasoning logs to the terminal, and post a formal review on GitHub.

*(Note: In a production environment, this endpoint would be connected to a GitHub Webhook to trigger automatically on `pull_request.opened` events.)*

-----


## 🛡️ License

MIT

```





