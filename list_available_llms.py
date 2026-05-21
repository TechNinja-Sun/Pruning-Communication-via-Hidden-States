"""Fetch and save all available LLM models from the configured OpenAI-compatible API.

Usage:
    python list_available_llms.py
    python list_available_llms.py --output-dir exp/result
    python list_available_llms.py --csv models.csv --md models.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
import os
from openai import OpenAI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List all callable LLM models and save as table files."
    )
    parser.add_argument(
        "--env-file",
        default="model.env",
        help="Path to env file (default: model.env)",
    )
    parser.add_argument(
        "--output-dir",
        default="exp/result",
        help="Directory for output files (default: exp/result)",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Custom CSV output path. If omitted, auto-generate with timestamp.",
    )
    parser.add_argument(
        "--md",
        default=None,
        help="Custom Markdown output path. If omitted, auto-generate with timestamp.",
    )
    return parser.parse_args()


def load_config(env_file: str) -> Dict[str, str]:
    load_dotenv(dotenv_path=env_file)
    base_url = os.getenv("BASE_URL", "").strip().strip('"')
    api_key = os.getenv("API_KEY", "").strip().strip('"')

    if not base_url:
        raise ValueError("BASE_URL is missing in env file.")
    if not api_key:
        raise ValueError("API_KEY is missing in env file.")

    return {"base_url": base_url, "api_key": api_key}


def fetch_models(base_url: str, api_key: str) -> List[Dict[str, Any]]:
    client = OpenAI(base_url=base_url, api_key=api_key)
    response = client.models.list()

    rows: List[Dict[str, Any]] = []
    for item in response.data:
        created = getattr(item, "created", None)
        created_str = (
            dt.datetime.fromtimestamp(created).isoformat(sep=" ", timespec="seconds")
            if isinstance(created, int)
            else ""
        )

        rows.append(
            {
                "id": getattr(item, "id", ""),
                "owned_by": getattr(item, "owned_by", ""),
                "object": getattr(item, "object", ""),
                "created": created_str,
            }
        )

    rows.sort(key=lambda x: str(x["id"]))
    return rows


def ensure_output_paths(args: argparse.Namespace) -> Dict[str, Path]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = Path(args.csv) if args.csv else output_dir / f"available_llms_{timestamp}.csv"
    md_path = Path(args.md) if args.md else output_dir / f"available_llms_{timestamp}.md"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    return {"csv": csv_path, "md": md_path}


def save_csv(rows: List[Dict[str, Any]], csv_path: Path) -> None:
    headers = ["id", "owned_by", "object", "created"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def save_markdown(rows: List[Dict[str, Any]], md_path: Path) -> None:
    headers = ["id", "owned_by", "object", "created"]
    lines = [
        "| id | owned_by | object | created |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['owned_by']} | {row['object']} | {row['created']} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    cfg = load_config(args.env_file)
    out = ensure_output_paths(args)

    rows = fetch_models(cfg["base_url"], cfg["api_key"])
    if not rows:
        print("No models returned by API.")
        return

    save_csv(rows, out["csv"])
    save_markdown(rows, out["md"])

    print(f"Done. Models count: {len(rows)}")
    print(f"CSV saved to: {out['csv']}")
    print(f"Markdown saved to: {out['md']}")


if __name__ == "__main__":
    main()
