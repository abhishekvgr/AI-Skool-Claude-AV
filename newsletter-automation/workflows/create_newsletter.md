# Workflow: Create Newsletter

## Objective
Turn a topic into a researched, illustrated HTML newsletter and save it as a Gmail draft for review.

## Inputs
- **Topic** (required). Default: "this week's most important AI news".
- **Recency**: `week` by default (weekly newsletter). Use `day` or `month` if asked.
- **Recipient**: optional; falls back to `GMAIL_TO` in `.env`. A draft with no recipient is fine.
- **Newsletter name**: default "AI Weekly".

## Setup check (once per run)
- `.env` has `PERPLEXITY_API_KEY` and `KIE_API_KEY`.
- `credentials.json` exists in the project root (Google OAuth Desktop client with the Gmail API enabled).
- Dependencies are installed: `pip install -r requirements.txt`.

## Steps

Pick a short slug for the run (for example `2026-10-22-ai-news`) and keep everything in `.tmp/<slug>/`.

### 1. Research (Perplexity)
```
python tools/research_topic.py --topic "<topic>" --recency week --out .tmp/<slug>/research.json
```
Read `research.json`. If the answer is thin or off-topic, rerun once with a sharper topic or `--preset high`.

### 2. Write the content (you, the agent)
Write `.tmp/<slug>/content.json` with this shape:
```json
{
  "newsletter_name": "AI Weekly",
  "issue_date": "October 22, 2026",
  "subject": "Email subject line, under 60 chars",
  "preheader": "One-line inbox preview, under 100 chars",
  "title": "Issue headline",
  "hero_image": "hero.png",
  "intro": "2-3 sentence hook.",
  "sections": [
    {"heading": "Story headline", "body": "Paragraphs separated by blank lines. Supports **bold**, *italic*, [links](https://...) and '- ' bullet lists.", "image": "infographic_1.png", "image_alt": "What the infographic shows"}
  ],
  "takeaways": ["Short bullet", "Short bullet"],
  "outro": "Sign-off line.",
  "sources": [{"title": "Source title", "url": "https://..."}]
}
```
Writing rules:
- Use only facts that appear in `research.json`. Every number, date and name must trace back to a source.
- 4-6 sections, each 80-150 words. Plain, confident tone; explain why each story matters.
- Link to the source inside the body where the claim is made, and list all used sources at the end.
- `hero_image` and section `image` fields are optional. Plan for 1 hero plus up to 2 section infographics, only where data or a process can be visualized.

### 3. Generate infographics (Nano Banana via Kie.ai — costs credits)
For each image named in `content.json`:
```
python tools/generate_infographic.py --prompt "<prompt>" --aspect-ratio 4:5 --out .tmp/<slug>/images/<file>
```
- Use `--aspect-ratio 16:9` for the hero image, `4:5` for section infographics.
- Prompt template: "Clean, modern editorial infographic about <subject>. Show <the 2-4 key facts or numbers, spelled out exactly>. Flat vector style, white background, indigo (#4f46e5) accent color, large legible sans-serif labels, minimal text, no logos."
- Keep text in the image short; image models garble long text. Spell out the exact numbers you want shown.
- The image file name minus its extension becomes the email's `cid:` reference, so file names must be unique.
- If a generation fails, read the error, and **ask the user before retrying** (each attempt spends credits).

### 4. Render HTML
```
python tools/render_newsletter.py --content .tmp/<slug>/content.json
```
Open `.tmp/<slug>/preview.html` in a browser to check it (`open .tmp/<slug>/preview.html`).

### 5. Create the Gmail draft
```
python tools/create_gmail_draft.py --content .tmp/<slug>/content.json [--to someone@example.com]
```
The first run opens a browser for Google sign-in and saves `token.json`. Never send the email; the user reviews and sends the draft.

## Output
A Gmail draft with inline images, plus the subject line and a short summary of the stories reported back to the user.

## Edge cases and lessons learned
- Perplexity's Sonar Chat Completions API was retired on 2026-09-27. `research_topic.py` uses the Agent API (`/v1/agent`, `preset` + `input`, recency via `tools[].filters`).
- Kie.ai returns HTTP 200 even on errors; the tool checks the `code` field. Code 402 means out of credits.
- Kie.ai image URLs expire after 14 days, which is why images are downloaded and embedded inline (CID) rather than hotlinked.
