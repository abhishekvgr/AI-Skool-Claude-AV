# Scrapper: Agent Instructions

This project is for **getting data off the web**: extracting content, structured fields, screenshots, crawling whole sites, mapping URLs, searching, and monitoring pages for change. Anything that involves pulling information from a website belongs here.

You have the **Firecrawl MCP server** (`mcp__firecrawl__*`). It is your primary instrument. Read [FIRECRAWL_CHEATSHEET.md](FIRECRAWL_CHEATSHEET.md) before choosing a tool; it has the quick chooser, params, gotchas, and decision flow.

## Picking a tool (short version)

| Goal | Tool |
|---|---|
| One known URL: content, screenshot, links, branding, or schema JSON | `firecrawl_scrape` |
| Unknown page / current info | `firecrawl_search`, then scrape the best hit |
| Every URL on a site | `firecrawl_map` |
| Content from many pages | `firecrawl_map` first, then `firecrawl_crawl` with `limit` + `includePaths` |
| Entity/dataset across unknown sources | `firecrawl_agent` (always set `maxCredits`) |
| Clicks, logins, forms, pagination | `firecrawl_interact` (then `firecrawl_interact_stop`) |
| Same fields across many entities | Alexandria: `firecrawl_find_tools`, then `firecrawl_scrape` with `alexandria` |
| Local PDF/Word/spreadsheet | `firecrawl_parse` |
| Detect changes over time | `firecrawl_monitor_*` |

Default to the cheapest tool that answers the question: scrape beats crawl, map beats blind crawling, search beats agent.

## Rules

1. **Credits are real money.** Run `firecrawl_credit_usage` before large jobs. Map before crawl, cap `limit`, set `maxCredits` on agents, leave `scrapeOptions` off `search` unless full text is needed, and use `maxAge` for stable pages.
2. **Ask before spending twice.** If a paid call fails, diagnose first and check with me before retrying. Ask before creating monitors (they schedule recurring paid checks) or any `interact` step that submits a form or has side effects on a live site.
3. **Confirm scale first.** For crawls or agents that could return hundreds of pages, tell me the expected size and cost, then proceed.
4. **Respect the sites.** Honor robots/terms, don't hammer servers, and don't scrape behind logins I haven't authorized. Escalate `proxy` (`stealth`/`enhanced`) only when a plain fetch is blocked.
5. **Verify output.** Check that scraped content is the real page (not a cookie wall, bot block, or empty JS shell). Retry with `waitFor` or `proxy` if so. Never invent fields the page didn't contain; report missing data as missing.
6. **Cite the source.** Keep the URL (and fetch date when freshness matters) alongside every extracted record.

## WAT structure

Probabilistic reasoning is yours; deterministic execution lives in code.

- `workflows/`: Markdown SOPs (objective, inputs, tools, outputs, edge cases). Read the relevant one first. Don't create or overwrite workflows without asking.
- `tools/`: Python scripts for repeatable processing. Check here before writing anything new.
- `.env`: all keys (`FIRECRAWL_API_KEY`, etc.). Never put secrets anywhere else, and don't print or commit them.
- `.tmp/`: disposable intermediates (raw scrapes, exports). Regenerable and gitignored.

**MCP vs Python:** Firecrawl MCP tools only run inside a Claude session. A script in `tools/` can't call them and must use the Firecrawl REST API with the key from `.env`. Use MCP for interactive and exploratory work; build a `tools/` script when a job needs to be repeatable or run unattended.

## Outputs

Final deliverables go where I can use them directly (Google Sheets/Docs, or a clearly named file I'm told about). Raw scrape dumps stay in `.tmp/`. Prefer structured output (JSON schema, CSV) over prose when the data is tabular.

## Self-improvement loop

When something breaks: read the full error, fix the tool or approach, verify, then record what you learned (rate limits, blocked sites, needed `waitFor`, working schemas) in the relevant workflow so it doesn't recur.
