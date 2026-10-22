"""Generate an infographic with Nano Banana via Kie.ai and download it locally.

Each run costs Kie.ai credits.

Usage:
    python tools/generate_infographic.py --prompt "..." --out .tmp/ai-agents/images/infographic_1.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.kie.ai/api/v1/jobs"
MODEL = "google/nano-banana"
ASPECT_RATIOS = ["1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9", "auto"]


def create_task(api_key: str, prompt: str, aspect_ratio: str, output_format: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/createTask",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output_format": output_format,
            },
        },
        timeout=60,
    )
    body = resp.json()
    # Kie.ai returns HTTP 200 even for errors, so check the body's code.
    if body.get("code") != 200:
        sys.exit(f"createTask failed ({body.get('code')}): {body.get('msg')}")
    return body["data"]["taskId"]


def wait_for_result(api_key: str, task_id: str, timeout: int) -> list[str]:
    delay, waited = 3.0, 0.0
    while waited < timeout:
        time.sleep(delay)
        waited += delay
        resp = requests.get(
            f"{BASE_URL}/recordInfo",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"taskId": task_id},
            timeout=30,
        )
        body = resp.json()
        if body.get("code") != 200:
            sys.exit(f"recordInfo failed ({body.get('code')}): {body.get('msg')}")
        data = body["data"]
        state = data.get("state")
        if state == "success":
            return json.loads(data["resultJson"])["resultUrls"]
        if state == "fail":
            sys.exit(f"Generation failed ({data.get('failCode')}): {data.get('failMsg')}")
        print(f"  {state}... ({int(waited)}s)")
        delay = min(delay * 1.5, 15)
    sys.exit(f"Timed out after {timeout}s waiting for task {task_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", required=True, help="Where to save the image")
    parser.add_argument("--aspect-ratio", default="4:5", choices=ASPECT_RATIOS)
    parser.add_argument("--format", default="png", choices=["png", "jpeg"])
    parser.add_argument("--timeout", type=int, default=300, help="Seconds to wait for the image")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        sys.exit("KIE_API_KEY is not set in .env")

    task_id = create_task(api_key, args.prompt, args.aspect_ratio, args.format)
    print(f"Created task {task_id}")
    urls = wait_for_result(api_key, task_id, args.timeout)

    img = requests.get(urls[0], timeout=120)
    img.raise_for_status()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(img.content)
    print(f"Saved image to {out}")


if __name__ == "__main__":
    main()
