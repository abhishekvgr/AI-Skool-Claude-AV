"""Research a topic with the Perplexity Agent API and save the findings + sources.

Usage:
    python tools/research_topic.py --topic "AI agents" --out .tmp/ai-agents/research.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://api.perplexity.ai/v1/agent"

INSTRUCTIONS = (
    "You are a research assistant for a weekly newsletter. Find the most important, "
    "recent developments on the topic. For each development give: what happened, who is "
    "involved, when, why it matters, and any concrete numbers (funding, benchmarks, "
    "users, dates). Prefer primary sources and reputable outlets. Cite every claim with "
    "inline [n] markers. Organize the answer under clear headings, 5-8 stories total."
)


def parse_response(body: dict) -> tuple[str, list[dict]]:
    """Pull the answer text and the source list out of an Agent API response."""
    text_parts: list[str] = []
    sources: list[dict] = []
    for item in body.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    text_parts.append(part.get("text", ""))
        elif item.get("type") == "search_results":
            for r in item.get("results", []):
                sources.append({
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "date": r.get("date"),
                    "snippet": r.get("snippet"),
                })
    text = "\n".join(text_parts) or body.get("output_text", "")
    return text, sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--out", required=True, help="Path to write research JSON")
    parser.add_argument("--recency", default="week", choices=["day", "week", "month", "year"])
    parser.add_argument("--preset", default="medium",
                        help="Agent API preset: fast, low, medium, high, xhigh")
    parser.add_argument("--max-results", type=int, default=20)
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        sys.exit("PERPLEXITY_API_KEY is not set in .env")

    payload = {
        "preset": args.preset,
        "instructions": INSTRUCTIONS,
        "input": f"Research the latest news and developments on: {args.topic}",
        "tools": [{
            "type": "web_search",
            "max_results": args.max_results,
            "filters": {"search_recency_filter": args.recency},
        }],
    }
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=300,
    )
    if resp.status_code != 200:
        sys.exit(f"Perplexity API error {resp.status_code}: {resp.text[:1000]}")

    body = resp.json()
    text, sources = parse_response(body)
    if not text:
        sys.exit(f"No answer text in response: {json.dumps(body)[:1000]}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "topic": args.topic,
        "recency": args.recency,
        "answer": text,
        "sources": sources,
        "usage": body.get("usage"),
    }, indent=2))
    print(f"Saved research ({len(text)} chars, {len(sources)} sources) to {out}")


if __name__ == "__main__":
    main()
