"""Generate demo walkthrough markdown with Playwright screenshots.

This helper starts the FastAPI demo app with demo data enabled, drives the
minimal HTML form with Playwright, and writes markdown files that link to
on-disk screenshots (no base64 embeds).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from playwright.async_api import Browser, async_playwright

BASE_PORT = 8000
DEFAULT_OUTPUT = Path("docs/generated_demos")

DemoConfig = Dict[str, Any]

DEMOS: List[DemoConfig] = [
    {
        "slug": "demo_user_system",
        "title": "Demo user system",
        "description": "Scalar-only user onboarding example with favorite color resolution.",
        "inputs": {
            "demo.user_name": "Alice Example",
            "demo.user_id": "42",
            "demo.favorite_color": "green",
        },
    },
    {
        "slug": "support_triage",
        "title": "Support triage",
        "description": "Route an incident summary to a support team with an ETA.",
        "inputs": {
            "demo.support.incident_summary": "Login button returns a 500 error",
            "demo.support.severity": "major",
            "demo.support.customer_impact": "Most users cannot log in",
        },
    },
    {
        "slug": "weather_planner",
        "title": "Weather planner",
        "description": "Plan a day outside based on temperature and precipitation.",
        "inputs": {
            "demo.weather.location": "Seattle, WA",
            "demo.weather.temperature_f": "68.0",
            "demo.weather.precip_probability": "0.35",
        },
    },
    {
        "slug": "vector_scalar_transition",
        "title": "Vector to scalar transition",
        "description": "Show a batch of users flowing into scalar representatives.",
        "inputs": {
            "vector_scalar.user_batch_relation": json.dumps(
                [
                    {"user_id": 1, "name": "Riley", "email": "riley@example.com"},
                    {"user_id": 2, "name": "Max", "email": "max@example.com"},
                ]
            ),
        },
    },
]


def wait_for_health(port: int, timeout: float = 30.0) -> None:
    """Poll the /health endpoint until the server is ready or timeout elapses."""

    start = time.time()
    url = f"http://127.0.0.1:{port}/health"
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return
        except urllib.error.URLError:
            time.sleep(0.5)
    raise RuntimeError("Demo server did not become ready before timeout")


def start_server(port: int) -> subprocess.Popen[bytes]:
    """Start uvicorn with demo data enabled and return the subprocess."""

    env = {**os.environ, "RESOLVER_INCLUDE_DEMO_DATA": "true"}
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "resolver_engine.app:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    process = subprocess.Popen(command, env=env)
    wait_for_health(port)
    return process


async def capture_demo(browser: Browser, base_url: str, output_dir: Path, demo: DemoConfig) -> None:
    screenshot_dir = output_dir / "screenshots" / demo["slug"]
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    page = await browser.new_page()
    await page.goto(base_url, wait_until="networkidle")

    for fact_id, value in demo.get("inputs", {}).items():
        locator = page.locator(f"input[name='{fact_id}']")
        if await locator.count() > 0:
            await locator.fill(str(value))

    screenshot_path = screenshot_dir / "form.png"
    await page.screenshot(path=screenshot_path.as_posix(), full_page=True)

    markdown_path = output_dir / f"{demo['slug']}.md"
    payload = json.dumps(demo.get("inputs", {}), indent=2)
    markdown = f"""# {demo['title']} demo walkthrough (automated)

This file was generated automatically with Playwright during the demo documentation workflow.

## Steps captured
1. Launch the resolver demo form with bundled demo data.
2. Fill representative values for {demo['title']} facts.
3. Capture a screenshot of the populated form.

## Screenshot
![{demo['title']} form](./screenshots/{demo['slug']}/form.png)

## Sample payload
```json
{payload}
```
"""
    markdown_path.write_text(markdown, encoding="utf-8")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo markdowns with Playwright")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Where to write markdown and screenshots")
    parser.add_argument("--port", type=int, default=BASE_PORT, help="Port to run the uvicorn server on")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    process = start_server(args.port)
    base_url = f"http://127.0.0.1:{args.port}/"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            for demo in DEMOS:
                await capture_demo(browser, base_url, args.output, demo)
            await browser.close()
    finally:
        process.terminate()
        process.wait(timeout=15)


if __name__ == "__main__":
    asyncio.run(main())
