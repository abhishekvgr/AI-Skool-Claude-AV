"""Scrape DailyRemote search results (listing cards + each job's detail page) into JSON and CSV.

Uses the Firecrawl REST API (FIRECRAWL_API_KEY in .env). Costs 1 credit per listing page
and 1 per job detail page; detail pages already saved in <out>/raw/ are reused for free.

Usage:
    python tools/scrape_dailyremote.py --search "data engineering" --limit 20 [--out .tmp/dailyremote]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
FIRECRAWL_URL = "https://api.firecrawl.dev/v2/scrape"
BASE = "https://dailyremote.com"

FIELDS = ["job_id", "title", "company", "job_url", "apply_url", "salary", "job_type", "location",
          "experience", "category", "posted", "skills", "summary", "description", "scrape_status", "scraped_at"]

CARD_RE = re.compile(r"(?m)^## \[(?P<title>[^\]]+)\]\((?P<url>https://dailyremote\.com/remote-job/[^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
META_RE = re.compile(
    r"^(?P<loc>.*?)"
    r"(?P<sal>\$?[\d,.]+K?\s*-\s*\$?[\d,.]+K? per (?:year|month|week|day|hour))?"
    r"(?P<exp>\d+(?:-\d+|\+) yrs exp)?"
    r"\s*(?P<cats>\[.*)?$"
)


def firecrawl(url: str, key: str) -> tuple[str, dict]:
    resp = requests.post(
        FIRECRAWL_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Firecrawl {resp.status_code} for {url}: {resp.text[:300]}")
    data = resp.json().get("data", {})
    return data.get("markdown", ""), data.get("metadata", {})


def job_id(url: str) -> str:
    return url.rstrip("/").rsplit("-", 1)[-1]


def parse_listing(md: str) -> list[dict]:
    jobs = []
    matches = list(CARD_RE.finditer(md))
    for i, m in enumerate(matches):
        body = md[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(md)]
        body = body.split("[APPLY]", 1)[0]
        lines = [l.strip() for l in body.split("\n") if l.strip()]
        job = {"job_id": job_id(m["url"]), "title": m["title"].strip(), "job_url": m["url"]}

        # lines[0] = "Company hidden", lines[1] = "·Full Time·1 hour ago", lines[2] = location/salary/exp/category
        type_line = next((l for l in lines if l.startswith("·")), "")
        bits = [b.strip() for b in type_line.split("·") if b.strip()]
        job["job_type"] = bits[0] if bits else ""
        job["posted"] = bits[1] if len(bits) > 1 else ""

        meta_idx = lines.index(type_line) + 1 if type_line in lines else 2
        meta = META_RE.match(lines[meta_idx]) if meta_idx < len(lines) else None
        if meta:
            job["location"] = meta["loc"].strip()
            job["salary"] = (meta["sal"] or "").strip()
            job["experience"] = (meta["exp"] or "").replace(" exp", "")
            job["category"] = ", ".join(t for t, _ in LINK_RE.findall(meta["cats"] or ""))

        rest = lines[meta_idx + 1:]
        tag_lines = [l for l in rest if l.startswith("[") and "-jobs)" in l]
        job["skills"] = ", ".join(t for l in tag_lines for t, _ in LINK_RE.findall(l))
        job["summary"] = " ".join(l for l in rest if l not in tag_lines)
        jobs.append(job)
    return jobs


def parse_detail(md: str, meta: dict) -> dict:
    out = {}
    company = re.search(r"\*\*([^*]+)\*\*\]\(https://dailyremote\.com/remote-company/", md)
    if company:
        out["company"] = company[1].strip()
    elif " at " in meta.get("title", ""):
        out["company"] = meta["title"].rsplit(" at ", 1)[1].strip()

    apply = re.search(r"\[Apply Now\]\((https://dailyremote\.com/apply/[^)]+)\)", md)
    out["apply_url"] = apply[1] if apply else ""

    desc = md.split("AI Summary", 1)[1] if "AI Summary" in md else ""
    desc = desc.split("Share this job", 1)[0].strip()
    # Drop the AI summary paragraph itself; the listing card already has it.
    desc = desc.split("\n\n", 1)[1] if "\n\n" in desc else desc
    desc = re.sub(r"\n{3,}", "\n\n", desc.replace("**", "").replace("\\*", "*"))
    out["description"] = desc.strip()[:45000]

    out["scrape_status"] = "ok" if re.search(r"(?m)^# ", md) and meta.get("statusCode") == 200 else "check: no title/blocked"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--search", default="data engineering")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--out", default=".tmp/dailyremote")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    key = os.getenv("FIRECRAWL_API_KEY")
    if not key:
        sys.exit("FIRECRAWL_API_KEY missing from .env")

    out = ROOT / args.out
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    credits = 0

    jobs: list[dict] = []
    page = 1
    while len(jobs) < args.limit:
        url = f"{BASE}/?{urlencode({'search': args.search, 'page': page})}"
        md, meta = firecrawl(url, key)
        credits += meta.get("creditsUsed", 1)
        (raw / f"listing_p{page}.md").write_text(md)
        found = parse_listing(md)
        print(f"listing page {page}: {len(found)} jobs")
        if not found:
            break
        seen = {j["job_id"] for j in jobs}
        jobs += [j for j in found if j["job_id"] not in seen]
        page += 1
    jobs = jobs[: args.limit]

    for n, job in enumerate(jobs, 1):
        cache = raw / f"job_{job['job_id']}.json"
        if cache.exists():
            cached = json.loads(cache.read_text())
            md, meta = cached["markdown"], cached["metadata"]
            note = "cached"
        else:
            try:
                md, meta = firecrawl(job["job_url"], key)
            except RuntimeError as e:
                print(f"  [{n}/{len(jobs)}] FAILED {job['job_url']}: {e}")
                job["scrape_status"] = "failed"
                continue
            credits += meta.get("creditsUsed", 1)
            cache.write_text(json.dumps({"markdown": md, "metadata": meta}))
            note = f"{meta.get('creditsUsed', 1)} credit"
            time.sleep(0.5)
        job.update(parse_detail(md, meta))
        job["scraped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"  [{n}/{len(jobs)}] {job['title']} @ {job.get('company', '?')} ({note})")

    (out / "jobs.json").write_text(json.dumps(jobs, indent=2, ensure_ascii=False))
    with open(out / "jobs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(jobs)

    flagged = [j["job_id"] for j in jobs if j.get("scrape_status") != "ok"]
    print(f"\n{len(jobs)} jobs -> {out / 'jobs.csv'}")
    print(f"Firecrawl credits used this run: {credits}")
    if flagged:
        print(f"Needs a look (blocked/failed/no title): {', '.join(flagged)}")


if __name__ == "__main__":
    main()
