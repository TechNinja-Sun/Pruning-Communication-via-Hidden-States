from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import List

from system.registry import PRUNE_COMM_REGISTRY

from llm.openai_chat_base import OpenAIChatBase


def _is_registered(model_name: str) -> bool:
    try:
        PRUNE_COMM_REGISTRY.get_class(model_name)
        return True
    except Exception:
        return False


def _sanitize_class_name(model_name: str) -> str:
    class_name = re.sub(r"[^0-9a-zA-Z_]", "_", model_name)
    if class_name and class_name[0].isdigit():
        class_name = f"Model_{class_name}"
    return f"{class_name}Chat"


def _discover_model_names() -> List[str]:
    root_dir = Path(__file__).resolve().parents[2]
    csv_candidates = []

    # Support both root-level exports and exp/result exports.
    csv_candidates.extend(root_dir.glob("available_llms_*.csv"))
    csv_candidates.extend((root_dir / "exp" / "result").glob("available_llms_*.csv"))

    csv_files = sorted(
        [p for p in csv_candidates if p.exists()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not csv_files:
        return []

    model_names: List[str] = []
    seen = set()

    with csv_files[0].open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            model_name = (row.get("id") or "").strip()
            if not model_name or model_name in seen:
                continue
            seen.add(model_name)
            model_names.append(model_name)

    return model_names


def _build_and_register(model_name: str):
    class_name = _sanitize_class_name(model_name)

    class GeneratedChat(OpenAIChatBase):
        def __init__(self, model_name: str = model_name):
            super().__init__(model_name)

    GeneratedChat.__name__ = class_name
    GeneratedChat.__qualname__ = class_name
    PRUNE_COMM_REGISTRY.register(model_name)(GeneratedChat)
    return GeneratedChat


def register_available_models() -> List[str]:
    registered_models: List[str] = []
    model_names = _discover_model_names()

    for model_name in model_names:
        if _is_registered(model_name):
            continue
        _build_and_register(model_name)
        registered_models.append(model_name)

    return registered_models


register_available_models()
