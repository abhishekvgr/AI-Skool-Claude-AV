# Firecrawl Cheat Sheet

What each Firecrawl MCP tool does and when to pick it. Tool names are as they appear in Claude sessions (`mcp__firecrawl__<name>`).

> **MCP vs Python:** these tools only run inside a Claude session. A WAT script in `tools/` can't call them, so it would use the Firecrawl REST API with a `FIRECRAWL_API_KEY` in `.env`. Decide which side a step belongs on before building it.

## Quick chooser

| I want to... | Use |
|---|---|
| Read one page I have the URL for | `firecrawl_scrape` |
| Pull specific fields from one page | `firecrawl_scrape` with `formats: ["json"]` + schema |
| Find pages about a topic | `firecrawl_search` |
| List every URL on a site | `firecrawl_map` |
| Get content from many pages of one site | `firecrawl_crawl` (run `map` first to size it) |
| Research an entity or build a dataset when I don't know the URLs | `firecrawl_agent` |
| Click, type, log in, or paginate before reading | `firecrawl_interact` |
| Read a local PDF/Word/spreadsheet | `firecrawl_parse` |
| Code, library, or error-message questions | `firecrawl_developer_search` |
| Statutes, regulations, court opinions | `firecrawl_gov_search` |
| Biomedical or arXiv papers | `firecrawl_research_*` |
| Same fields across many entities (companies, jobs, prices) | Alexandria via `firecrawl_find_tools` |
| Be told when a page changes | `firecrawl_monitor_*` |
| Check remaining credits | `firecrawl_credit_usage` |

## Core tools

### `firecrawl_scrape`
Fetch **one URL** and return it as markdown (default), html, links, images, screenshot, summary, branding, a targeted `query` answer, or JSON matching a schema.
- **Use when:** you know the page. This is the default tool.
- **Avoid when:** the URL is unknown (search/map first) or you need many pages (crawl).
- **Key params:** `formats`, `onlyMainContent`, `waitFor` (JS-heavy pages), `maxAge` (`0` = live fetch, otherwise cached results are allowed), `proxy` (`basic`/`stealth`/`enhanced`/`auto` for blocked sites), `includeTags`/`excludeTags`, `jsonOptions.schema`, `location`.
- **Cost:** 1 credit for a basic scrape (seen in the live test).
- **Also:** with an `alexandria` body it runs provider capabilities instead of fetching a page (see Alexandria below).

### `firecrawl_search`
Web, news, or image search. Returns title, URL, and query-relevant highlights per result.
- **Use when:** you need current info or don't know which page has the answer.
- **Key params:** `query`, `limit`, `sources` (`web`/`news`/`images`), `categories` (`research`, `pdf`, `developer`, `gov`), `includeDomains`/`excludeDomains` (mutually exclusive), `tbs` for time filtering, `location`.
- **Gotcha:** `scrapeOptions` fetches the full page of every result and bills a scrape each. Leave it off unless you need full text; scrape the one or two URLs you care about instead.
- **Also:** authenticated searches add matching Alexandria providers in `data.tools`.

### `firecrawl_map`
Return a site's **URL list** without fetching content.
- **Use when:** you need to find the right page on a site, or size a crawl before paying for it.
- **Key params:** `url`, `search` (narrow by term), `sitemap` (`include`/`skip`/`only`), `includeSubdomains`, `limit`, `ignoreQueryParameters`.

### `firecrawl_crawl`
Crawl many pages from a start URL and return their content. In this MCP it starts the job and polls to completion for you.
- **Use when:** you need the content of a section or whole site (docs, blog, catalog).
- **Key params:** `limit`, `maxDiscoveryDepth`, `includePaths`/`excludePaths`, `crawlEntireDomain`, `allowSubdomains`, `allowExternalLinks`, `sitemap`, `delay`, `maxConcurrency`, `deduplicateSimilarURLs`, `scrapeOptions` (same options as scrape, applied per page), `prompt`.
- **Gotcha:** results can be large and cost one scrape per page. Always set a conservative `limit` and path filters.

### `firecrawl_check_crawl_status`
Look up a crawl by its ID.
- **Use when:** a crawl was started elsewhere or you need to re-read its result.

### `firecrawl_agent` + `firecrawl_agent_status`
An autonomous research agent. You describe the fields you want in `prompt` (optionally a JSON `schema` and seed `urls`); it searches, navigates, and returns structured JSON assembled across sources.
- **Use when:** URLs are unknown or the answer spans several sites (an entity plus its fields, lists, datasets).
- **Avoid when:** you know the URL (scrape) or a results page answers it (search).
- **Flow:** `firecrawl_agent` returns only a job ID. Poll `firecrawl_agent_status` until `completed` or `failed`; a run typically takes 1 to 3 minutes.
- **Key params:** `prompt`, `schema`, `urls`, `strictConstrainToURLs`, `effort` (`low`/`medium`/`high`), **`maxCredits`** (cap spend; the default is high), `threadId` to continue a conversation.

### `firecrawl_interact` + `firecrawl_interact_stop`
Drive a **live browser session**: navigate, click, fill fields, or run code.
- **Use when:** the data is behind clicks, forms, infinite scroll, logins, or pagination.
- **Key params:** `url` or `scrapeId` (reuse an earlier scrape's session), then a natural-language `prompt` or `code` (`bash`/`python`/`node`), `timeout` (max 300 s), `profile` for saved sign-ins.
- **Gotcha:** it acts on the real site. Submitting a form creates real side effects. Call `firecrawl_interact_stop` to end the session.

### `firecrawl_parse`
Turn a **supplied file** (PDF, Word, RTF, OpenDocument, spreadsheet, HTML) into markdown, summary, a `query` answer, or schema JSON.
- **Use when:** the document is a local file. Remote URLs, including PDFs, go through `firecrawl_scrape`.
- **Key params:** `filePath`, `formats`, `pdfOptions.maxPages`, `redactPII`.
- **Note:** hosted MCP is two calls (get upload instructions, upload, then call again with `uploadRef`).

## Specialised search

| Tool | Use for |
|---|---|
| `firecrawl_developer_search` | Public repos, GitHub issues, merged PRs, READMEs, code docs. Same as `firecrawl_search` with `categories: ["developer"]`. |
| `firecrawl_gov_search` | US federal, state, and local primary law: statutes, regulations, codes, opinions. Check issuer, jurisdiction, status, and version before citing. |
| `firecrawl_research_search_papers` | Search PubMed, bioRxiv, medRxiv, and arXiv abstracts and full text. Different from `firecrawl_search` with `categories: ["research"]`, which only filters ordinary web results. |
| `firecrawl_research_inspect_paper` | Look at a paper's structure/metadata before reading it. |
| `firecrawl_research_read_paper` | Read a paper's full text. |
| `firecrawl_research_related_papers` | Find papers related to a known one. |

## Alexandria data providers

Firecrawl's catalogue of data providers (companies, people, jobs, finance and filings, public records, real estate, places, prices, package registries, news, research). They return typed, sourced records rather than scraped pages.

- **Discover (free):** `firecrawl_find_tools`. Call it with no arguments to browse categories, with `query` for semantic lookup, or with `urls` to find providers for a website. `includeCosts: true` shows credit prices.
- **Execute:** `firecrawl_scrape` with `alexandria: [{provider, capability, options}]` (up to 10 per call). Individual capabilities can fail even when the outer call succeeds.
- **Use when:** you need the same fields across many entities, exact figures, timestamps, or provenance. Prefer a provider over scraping page by page.
- **Gotcha:** some providers need terms accepted by an org admin in the Firecrawl dashboard.

## Monitoring

Recurring checks that compare each run with the last and can notify by email or webhook.

| Tool | Purpose |
|---|---|
| `firecrawl_monitor_create` | Create one. Simple form: `page`/`pages` or `queries` plus a plain-language `goal`, optional `scheduleText`, `email`, `webhookUrl`. Advanced form: `body`. |
| `firecrawl_monitor_list` / `_get` | See existing monitors and their details. |
| `firecrawl_monitor_update` / `_delete` | Change or remove one. |
| `firecrawl_monitor_run` | Trigger a check now. |
| `firecrawl_monitor_check` / `_checks` | Read one check result, or the history of checks. |

- **Gotcha:** a monitor schedules future paid network checks. Confirm the schedule before creating.

## Account and feedback

| Tool | Purpose |
|---|---|
| `firecrawl_credit_usage` | Current balance (`remainingCredits`, billing period) or 90-day history, optionally split `byEndpoint` or `byApiKey`. |
| `firecrawl_feedback` / `firecrawl_search_feedback` | Report result quality back to Firecrawl. Optional. |

## Decision flow

```
Know the exact URL?
├─ yes → needs clicks/login first? ── yes → interact
│                                  └─ no  → scrape
└─ no  → know the site?
         ├─ yes → map (find the page) → scrape, or crawl for many pages
         └─ no  → one fact/page?       → search → scrape the best hit
                  dataset/entity fields → agent (or Alexandria provider)
Need it repeatedly / on change?  → monitor
```

## Keeping credits under control

1. `map` before `crawl`, then crawl with `limit` and `includePaths`.
2. Don't use `scrapeOptions` on `search` unless you need full text.
3. Set `maxCredits` on every `agent` call.
4. Use `maxAge` for repeat reads of stable pages; use `maxAge: 0` only when freshness matters.
5. Check `firecrawl_credit_usage` before large jobs.
6. Per WAT rules in [CLAUDE.md](CLAUDE.md): ask before re-running anything that costs credits after a failure.
