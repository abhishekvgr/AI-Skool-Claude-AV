# Scrape DailyRemote jobs → Google Sheet

## Objective
Turn a DailyRemote job search into a Google Sheet with one row per job, including the company and the full description from each job's own page.

## Inputs
- Search term (e.g. `data engineering`, the same as `?search=` on dailyremote.com)
- Number of jobs (`--limit`)

## Steps
1. Check credits (`firecrawl_credit_usage`). Cost is about **1 credit per listing page (30 jobs) + 1 per job**. Detail pages already in `.tmp/dailyremote/raw/` are reused for free.
2. For a new search or after a site change, do a test run first: `--limit 2` (about 3 credits).
3. Scrape:
   ```bash
   .venv/bin/python tools/scrape_dailyremote.py --search "data engineering" --limit 20
   ```
   Outputs `.tmp/dailyremote/jobs.json` and `jobs.csv`, and prints the credits used plus any rows flagged for a look.
4. Push:
   ```bash
   .venv/bin/python tools/push_to_sheets.py --csv .tmp/dailyremote/jobs.csv [--title "..."] [--sheet-id <id>]
   ```
   Without `--sheet-id` it creates a new spreadsheet. With it, the first tab is overwritten. It prints the sheet URL.

## Columns
Job ID, Title, Company, Job URL, Apply URL, Salary, Job Type, Location, Experience, Category, Posted, Skills, Summary, Description, Scrape Status, Scraped At.

## Quirks (learned 2026-10-22)
- Listing cards show **"Company hidden"** (premium paywall). The company only appears on the detail page, which is why each job is opened.
- **Salary is on the listing card**, not reliably on the detail page. It's optional, and is sometimes non-USD with no `$` (e.g. `1500K - 2000K per year` for India).
- The card's meta line runs together with no separators: `United States$133K - $199K per year5-10 yrs exp [Category]`. The salary regex must end at a fixed unit (`per year|month|week|day|hour`), or it swallows the first digit of the experience.
- Apply links (`/apply/<id>?nonce=...`) carry a nonce and may expire. The Job URL is the stable link.
- "Posted" is relative ("Yesterday", "3 Days Ago"), so use `scraped_at` to anchor it.
- Descriptions contain line breaks, and Sheets grows rows to fit them even with clipped text (about 800px rows). `push_to_sheets.py` pins data rows to 21px.
- For a screenshot of the sheet, export it as a PDF through `https://docs.google.com/spreadsheets/d/<id>/export?format=pdf&gid=0&range=B1:L21` with the OAuth token, then `sips` it to PNG. A headless browser can't open the private sheet.
- The site lists near-duplicate postings (same title, different IDs). They are kept, since they are separate listings.
- `.env` key must be named `FIRECRAWL_API_KEY`. Google auth uses `credentials.json` (copied from newsletter-automation) plus its own `token.json` with the Sheets scope. The Google Sheets API must be enabled in that GCP project.
