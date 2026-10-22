"""Render newsletter content (JSON) into email-safe HTML.

Writes two files next to each other:
  newsletter.html  images referenced as cid:<name> (for the Gmail draft)
  preview.html     images referenced by relative path (open in a browser to review)

Usage:
    python tools/render_newsletter.py --content .tmp/ai-agents/content.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ACCENT = "#4f46e5"
TEXT = "#1f2937"
MUTED = "#6b7280"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def inline_md(text: str) -> str:
    """Escape text, then support **bold**, *italic* and [label](url)."""
    out = html.escape(text, quote=False)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                 # URL is already escaped by the html.escape above.
                 lambda m: f'<a href="{m.group(2)}" style="color:{ACCENT};">{m.group(1)}</a>',
                 out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", out)
    return out


def paragraphs(text: str) -> str:
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    rendered = []
    for b in blocks:
        lines = b.splitlines()
        if all(line.lstrip().startswith(("- ", "* ")) for line in lines):
            items = "".join(f'<li style="margin:0 0 6px;">{inline_md(line.lstrip()[2:])}</li>' for line in lines)
            rendered.append(f'<ul style="margin:0 0 16px;padding-left:20px;">{items}</ul>')
        else:
            rendered.append(f'<p style="margin:0 0 16px;">{inline_md(" ".join(lines))}</p>')
    return "".join(rendered)


def image_tag(filename: str, alt: str, mode: str) -> str:
    src = f"cid:{Path(filename).stem}" if mode == "email" else f"images/{filename}"
    return (f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" width="552" '
            f'style="display:block;width:100%;max-width:552px;height:auto;border-radius:8px;margin:0 0 16px;">')


def render(content: dict, mode: str) -> str:
    sections = []
    for s in content.get("sections", []):
        img = image_tag(s["image"], s.get("image_alt", s["heading"]), mode) if s.get("image") else ""
        sections.append(
            f'<h2 style="font-size:20px;line-height:1.3;margin:32px 0 12px;color:{TEXT};">{inline_md(s["heading"])}</h2>'
            f'{img}{paragraphs(s["body"])}'
        )

    takeaways = ""
    if content.get("takeaways"):
        items = "".join(f'<li style="margin:0 0 8px;">{inline_md(t)}</li>' for t in content["takeaways"])
        takeaways = (
            f'<div style="background:#eef2ff;border-radius:8px;padding:20px 24px;margin:32px 0 0;">'
            f'<h2 style="font-size:18px;margin:0 0 12px;color:{ACCENT};">Key takeaways</h2>'
            f'<ul style="margin:0;padding-left:20px;">{items}</ul></div>'
        )

    sources = ""
    if content.get("sources"):
        items = "".join(
            f'<li style="margin:0 0 4px;"><a href="{html.escape(src["url"])}" style="color:{MUTED};">'
            f'{html.escape(src.get("title") or src["url"])}</a></li>'
            for src in content["sources"]
        )
        sources = (f'<h3 style="font-size:14px;margin:32px 0 8px;color:{MUTED};">Sources</h3>'
                   f'<ol style="margin:0;padding-left:20px;font-size:13px;color:{MUTED};">{items}</ol>')

    hero = image_tag(content["hero_image"], content["title"], mode) if content.get("hero_image") else ""
    preheader = html.escape(content.get("preheader", ""))

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(content["subject"])}</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;">
<div style="display:none;max-height:0;overflow:hidden;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#ffffff;border-radius:12px;">
<tr><td style="padding:32px 24px;font-family:{FONT};font-size:16px;line-height:1.6;color:{TEXT};">
<p style="margin:0 0 4px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:{ACCENT};font-weight:600;">{html.escape(content.get("newsletter_name", "AI Weekly"))} &middot; {html.escape(content.get("issue_date", ""))}</p>
<h1 style="font-size:28px;line-height:1.25;margin:0 0 20px;color:{TEXT};">{inline_md(content["title"])}</h1>
{hero}
{paragraphs(content.get("intro", ""))}
{"".join(sections)}
{takeaways}
{paragraphs(content.get("outro", ""))}
{sources}
</td></tr></table>
</td></tr></table>
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", required=True, help="Path to content.json")
    args = parser.parse_args()

    content_path = Path(args.content)
    content = json.loads(content_path.read_text())
    out_dir = content_path.parent
    (out_dir / "newsletter.html").write_text(render(content, "email"))
    (out_dir / "preview.html").write_text(render(content, "preview"))
    print(f"Wrote {out_dir / 'newsletter.html'} and {out_dir / 'preview.html'}")


if __name__ == "__main__":
    main()
