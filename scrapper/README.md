# Scrapper

Web scraping project. Scope to be defined.

Built on the WAT framework (Workflows, Agents, Tools). See [CLAUDE.md](CLAUDE.md).

## Layout

```
workflows/   Step-by-step SOPs the agent follows
tools/       Python scripts that do the scraping and processing
```

Reference: [Firecrawl cheat sheet](FIRECRAWL_CHEATSHEET.md), what each Firecrawl tool does and when to use it.

Example runs:
- [DailyRemote data engineering jobs → Google Sheet](examples/2026-10-22-dailyremote-data-engineering/README.md), 20 jobs for 24 Firecrawl credits.
- [clawd.bot screenshots → branding breakdown](examples/2026-10-22-openclaw-branding/README.md), full-page screenshots and a brand analysis from 1 scrape.
- [Blue Bottle Coffee site map + homepage look](examples/2026-10-22-bluebottle-sitemap/README.md), 452 URLs grouped by purpose plus a full-page screenshot, for 2 Firecrawl credits.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
```
