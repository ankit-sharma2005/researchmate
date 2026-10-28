# ResearchMate

> Search. Read. Write. Review. All by AI agents.

ResearchMate is a multi-agent research tool. Enter a topic and it searches the
web, reads the top sources, writes a structured report, has a critic review
and improve it, and then fact-checks every claim against the sources.

## Features

- **Multi-step pipeline:** search, scrape, write, critique, revise, verify
- **Trust score:** extracts claims from the report and checks each one against the retrieved sources
- **Fake URL detection:** flags cited links that never appeared in the research
- **Depth levels:** Quick, Standard or Deep (more sources, more revision rounds)
- **Multi-perspective mode:** compares different viewpoints on contested topics
- **Live progress:** step-by-step progress while the job runs in the background
- **Django web app:** signup/login, dark mode, markdown report view, downloadable report

## How it works

1. **Search:** Tavily API finds sources (title, URL, snippet)
2. **Scrape:** requests + BeautifulSoup extract clean text from the top pages
3. **Write:** a LangChain chain with a local LLM (Ollama, llama3.2) drafts the report
4. **Critic and revise:** the critic scores the report out of 10; below 8 it is rewritten using the feedback
5. **Verify:** claims are checked against the sources, producing a trust score
6. **Perspectives (optional):** sources are grouped by viewpoint

The Django UI runs the pipeline in a background thread and the browser
polls for progress every 1.5 seconds.

## Tech stack

Python, Django, LangChain, Ollama (llama3.2), Tavily API, requests,
BeautifulSoup, Bootstrap 5.3, JavaScript, SQLite

## Setup

    git clone <your-repo-url>
    cd <repo-folder>
    python -m venv .venv
    .venv\Scripts\activate            # Windows
    pip install -r requirements.txt

    # create a .env file in the project root
    TAVILY_API_KEY=your_key

    ollama pull llama3.2
    ollama serve

    cd ui
    python manage.py migrate
    python manage.py runserver

Open http://127.0.0.1:8000/ and sign up.

## Limitations

- The trust score is an LLM-based estimate, not a guarantee
- A small local model can misjudge claims
- Jobs are stored in memory (lost on restart); use Celery + Redis in production
- No automated tests yet

## Roadmap

- LangGraph pipeline
- Report history saved per user
- Evaluation set and automated tests
- Docker and deployment
