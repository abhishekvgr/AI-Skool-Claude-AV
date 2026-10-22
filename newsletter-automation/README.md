# Newsletter Automation

Give it a topic and it produces a finished newsletter as a Gmail draft:

1. **Research**: Perplexity Agent API finds this week's developments, with sources.
2. **Write**: Claude writes the issue from the research.
3. **Illustrate**: Nano Banana (via Kie.ai) generates infographics.
4. **Format**: the content is rendered into email-safe HTML.
5. **Deliver**: a Gmail draft is created with images embedded inline, ready to review and send.

Built on the WAT framework (Workflows, Agents, Tools). See [CLAUDE.md](CLAUDE.md).

## Layout

```
workflows/create_newsletter.md   Step-by-step SOP the agent follows
tools/research_topic.py          Perplexity research -> research.json
tools/generate_infographic.py    Nano Banana image via Kie.ai -> PNG
tools/render_newsletter.py       content.json -> newsletter.html + preview.html
tools/create_gmail_draft.py      newsletter.html -> Gmail draft
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
```

You need:
- A **Perplexity API key** (https://www.perplexity.ai/account/api)
- A **Kie.ai API key** with credits (https://kie.ai/api-key)
- A **Google OAuth client** for Gmail:
  1. In Google Cloud Console, create a project and enable the **Gmail API**.
  2. Configure the OAuth consent screen (External, Testing) and add your Gmail address as a **test user**. Without this, sign-in fails with "Access blocked".
  3. Create an OAuth client ID of type **Desktop app** and download it as `credentials.json` into this folder.

## Usage

Open this folder in Claude Code and say:

> Create this week's newsletter on AI news

Claude follows `workflows/create_newsletter.md` and runs the tools in order.
