import re
from agent import (writer_chain, critic_chain, revise_chain,
                   claims_chain, verify_chain, perspective_chain)
from tools import search_web, scrap_url

# How many sources / revisions each depth level uses
DEPTH_CONFIG = {
    "quick":    {"search_results": 3, "scrape_urls": 1, "revise_rounds": 0},
    "standard": {"search_results": 5, "scrape_urls": 2, "revise_rounds": 1},
    "deep":     {"search_results": 8, "scrape_urls": 4, "revise_rounds": 3},
}

def parse_score(feedback: str):
    """Extract the 'score : x/10' number from the critic's text."""
    m = re.search(r"score\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback, re.I)
    return float(m.group(1)) if m else None

def verify_report(report: str, evidence: str) -> dict:
    """Check each claim against the evidence and find invented URLs."""
    raw = claims_chain.invoke({"report": report})
    claims = []
    for line in raw.splitlines():
        # remove bullets / numbering at the start of the line
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
        if len(line) > 15:
            claims.append(line)
    claims = claims[:8]  # limit to 8 claims to keep it fast

    results = []
    for claim in claims:
        verdict = verify_chain.invoke({"claim": claim, "evidence": evidence[:6000]})
        results.append({"claim": claim,
                        "supported": verdict.strip().upper().startswith("SUPPORTED")})

    supported = sum(r["supported"] for r in results)
    score = round(100 * supported / len(results)) if results else None

    # URLs in the report that never appeared in the research are invented
    cited = set(re.findall(r"https?://[^\s)\]>\"']+", report))
    fake_urls = [u for u in cited if u.rstrip(".,") not in evidence]

    return {"score": score, "claims": results, "fake_urls": fake_urls}

def run_research_pipeline(topic: str, depth: str = "standard",
                          perspectives: bool = False, progress=None) -> dict:
    # NEW: 'progress' is an optional callback function(step, text).
    # The Django background job passes it so the UI can show live progress.
    def notify(step, text):
        print(text)                    # still prints in the terminal
        if progress:
            progress(step, text)       # tells the UI which step is running

    cfg = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["standard"])
    state = {"depth": depth, "perspectives_on": perspectives}

    # ---- Step 1: search ----
    notify(1, "Searching the web for sources...")
    if perspectives:
        # three searches with different angles so sources differ in viewpoint
        queries = [topic,
                   f"{topic} criticism opposition view",
                   f"{topic} support defence view"]
        per_query = max(2, cfg["search_results"] // 2)
        state["search_results"] = "\n\n".join(search_web(q, per_query) for q in queries)
    else:
        state["search_results"] = search_web(topic, cfg["search_results"])

    # ---- Step 2: scrape the top URLs ----
    urls = list(dict.fromkeys(re.findall(r"https?://[^\s]+", state["search_results"])))
    urls = urls[: cfg["scrape_urls"] + (2 if perspectives else 0)]
    pages = []
    for i, u in enumerate(urls, 1):
        notify(2, f"Reading source {i} of {len(urls)}: {u[:60]}")
        pages.append(f"URL: {u}\n{scrap_url.invoke({'url': u})}")
    state["scraped_content"] = "\n\n".join(pages)

    research = (f"SEARCH RESULTS:\n{state['search_results']}\n\n"
                f"SCRAPED CONTENT:\n{state['scraped_content']}")

    # ---- Step 3: write the report ----
    notify(3, "Writing the report...")
    state["report"] = writer_chain.invoke({"topic": topic, "research": research})

    # ---- Step 4: critic review + revise loop ----
    notify(4, "Critic is reviewing the report...")
    state["feedback"] = critic_chain.invoke({"report": state["report"]})
    for i in range(cfg["revise_rounds"]):
        score = parse_score(state["feedback"])
        if score is not None and score >= 8:
            break  # good enough, stop early
        notify(4, f"Improving the report (round {i + 1})...")
        state["report"] = revise_chain.invoke({
            "topic": topic, "research": research,
            "report": state["report"], "feedback": state["feedback"],
        })
        state["feedback"] = critic_chain.invoke({"report": state["report"]})

    # ---- Step 5: verify claims on the FINAL report ----
    notify(5, "Checking claims against the sources...")
    state["verification"] = verify_report(state["report"], research)

    # ---- Step 6: multi-perspective comparison (optional) ----
    if perspectives:
        notify(6, "Comparing different viewpoints...")
        state["perspectives"] = perspective_chain.invoke(
            {"topic": topic, "research": research})

    return state

if __name__ == "__main__":
    topic = input("\nEnter a research topic : ")
    depth = input("Depth (quick/standard/deep) : ") or "standard"
    persp = input("Multi-perspective? (y/n) : ").lower() == "y"
    s = run_research_pipeline(topic, depth, persp)
    print("\nTRUST SCORE:", s["verification"]["score"], "%")