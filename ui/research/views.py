import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

import markdown
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from .forms import TopicForm
from .jobs import JOBS, start_job


ALLOWED_REPORT_TAGS = {
    "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4",
    "h5", "h6", "hr", "li", "ol", "p", "pre", "strong", "table", "tbody",
    "td", "th", "thead", "tr", "ul",
}
VOID_REPORT_TAGS = {"br", "hr"}


class ReportHTMLSanitizer(HTMLParser):
    """Allow a small set of safe HTML elements in rendered report markdown."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_REPORT_TAGS:
            return

        safe_attrs = []
        for name, value in attrs:
            if value is None:
                continue
            if tag == "a" and name == "href":
                if urlparse(value).scheme.lower() in {"", "http", "https", "mailto"}:
                    safe_attrs.append(f'href="{escape(value, quote=True)}"')
            elif tag == "a" and name == "title":
                safe_attrs.append(f'title="{escape(value, quote=True)}"')
            elif tag == "code" and name == "class" and re.fullmatch(
                r"language-[\w+-]+", value
            ):
                safe_attrs.append(f'class="{escape(value, quote=True)}"')

        attributes = f" {' '.join(safe_attrs)}" if safe_attrs else ""
        self.parts.append(f"<{tag}{attributes}>")

    def handle_endtag(self, tag):
        if tag in ALLOWED_REPORT_TAGS and tag not in VOID_REPORT_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(escape(data))


def render_report_markdown(report):
    """Render markdown using the existing safe subset of report HTML."""
    rendered = markdown.markdown(report, extensions=["extra"])
    sanitizer = ReportHTMLSanitizer()
    sanitizer.feed(rendered)
    return mark_safe("".join(sanitizer.parts))


@login_required
def index(request):
    """Render the research form without starting pipeline work."""
    form = TopicForm()
    return render(request, "research/index.html", {"form": form, "depth": "standard"})


@login_required
def start(request):
    """Validate a submitted topic and queue its research job."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    topic = request.POST.get("topic", "").strip()
    depth = request.POST.get("depth", "standard")
    if depth not in ("quick", "standard", "deep"):
        depth = "standard"
    if not topic:
        return JsonResponse({"error": "Please enter a topic."}, status=400)

    perspectives = "perspectives" in request.POST
    job_id = start_job(request.user.id, topic, depth, perspectives)
    return JsonResponse({"job_id": job_id, "perspectives": perspectives})


def _get_job(request, job_id):
    """Return a job only to its owner."""
    job = JOBS.get(job_id)
    if not job or job["user"] != request.user.id:
        raise Http404
    return job


@login_required
def status(request, job_id):
    """Return the latest progress for a user's job."""
    job = _get_job(request, job_id)
    data = {
        "status": job["status"],
        "step": job["step"],
        "message": job["message"],
        "error": job["error"],
    }
    if job["status"] == "done":
        data["result_url"] = reverse("research:result", args=[job_id])
    return JsonResponse(data)


@login_required
def result(request, job_id):
    """Render the completed research result."""
    job = _get_job(request, job_id)
    state = job["result"]
    if state is None:
        raise Http404

    report = str(state.get("report", ""))
    feedback = str(state.get("feedback", ""))
    score_match = re.search(
        r"(?:score\s*[:=-]?\s*)?(\d+(?:\.\d+)?)\s*(?:/10|out of 10)\b",
        feedback,
        flags=re.IGNORECASE,
    )
    score = score_match.group(1) if score_match else None
    perspectives_on = state.get("perspectives_on", False)
    context = {
        "topic": job.get("topic", ""),
        "depth": state.get("depth", "standard"),
        "search_results": state.get("search_results", ""),
        "scraped_content": state.get("scraped_content", ""),
        "report_html": render_report_markdown(report),
        "report_md": report,
        "report": report,
        "feedback": feedback,
        "score": score,
        "verification": state.get("verification"),
        "perspectives_on": perspectives_on,
    }
    if perspectives_on:
        context["perspectives"] = render_report_markdown(
            str(state.get("perspectives", ""))
        )
    return render(request, "research/result.html", context)


@login_required
@require_POST
def download_report(request):
    """Send the submitted report as a markdown download."""
    report = request.POST.get("report", "")
    topic = request.POST.get("topic", "research-report")
    safe_topic = re.sub(r"[^A-Za-z0-9_-]+", "-", topic).strip("-") or "research-report"

    response = HttpResponse(report, content_type="text/markdown; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{safe_topic}.md"'
    return response
