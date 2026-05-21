import asyncio
import json
import platform
import re
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

WORKSPACE_ROOT = Path(__file__).resolve().parent
sys.path.append(str(WORKSPACE_ROOT))

from PruneComm.system.workflow import Workflow as LiveWorkflow

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="PruneComm History API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EXP_ROOT = WORKSPACE_ROOT / "exp"


def _safe_json_load(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _round_number_from_path(path: Path) -> int:
    match = re.search(r"round_(\d+)\.json$", path.name)
    return int(match.group(1)) if match else 0


def _experiment_id(result_dir: Path, mode_dir: Path) -> str:
    return f"{result_dir.name}__{mode_dir.name}"


def _resolve_experiment_dir(experiment_id: str) -> Path:
    if "__" not in experiment_id:
        raise HTTPException(status_code=404, detail="Unknown experiment id")

    result_name, mode_name = experiment_id.split("__", 1)
    experiment_dir = EXP_ROOT / result_name / mode_name
    if not experiment_dir.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment_dir


def _sum_token_round(round_payload: dict[str, Any]) -> int:
    tokens = round_payload.get("tokens", {}) or {}
    return int(
        sum(
            int(token_info.get("first", 0)) + int(token_info.get("final", 0))
            for token_info in tokens.values()
        )
    )


def _upper_triangle_average(matrix: list[list[float]]) -> float:
    if not matrix:
        return 0.0

    values: list[float] = []
    for row_index, row in enumerate(matrix):
        for col_index, value in enumerate(row):
            if col_index > row_index:
                values.append(float(value))

    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _round_summary(round_payload: dict[str, Any]) -> dict[str, Any]:
    strategy = round_payload.get("hybrid_strategy", {}) or {}
    two_round_metrics = round_payload.get("two_round_metrics", {}) or {}

    return {
        "round": round_payload.get("round"),
        "question": round_payload.get("question", ""),
        "gt": round_payload.get("gt", ""),
        "pred": round_payload.get("pred", ""),
        "acc": round_payload.get("acc", 0.0),
        "strategy": strategy.get("active_strategy", ""),
        "consensus_option": strategy.get("consensus_option", ""),
        "consensus_ratio": strategy.get("consensus_ratio", 0.0),
        "high_threshold": strategy.get("high_threshold", 0.0),
        "mid_threshold": strategy.get("mid_threshold", 0.0),
        "correct_tendency": strategy.get("correct_tendency", False),
        "tokens": _sum_token_round(round_payload),
        "answer_change_rate": two_round_metrics.get("answer_change_rate", 0.0),
        "correction_rate": two_round_metrics.get("correction_rate", 0.0),
        "wrong_change_rate": two_round_metrics.get("wrong_change_rate", 0.0),
        "two_round_same_rate": two_round_metrics.get("two_round_same_rate", 0.0),
        "graph": round_payload.get("graph", {}),
        "secondary_graph": round_payload.get("secondary_graph", {}),
    }


def _scan_experiment_runs() -> list[dict[str, Any]]:
    if not EXP_ROOT.exists():
        return []

    runs: list[dict[str, Any]] = []

    for result_dir in sorted(EXP_ROOT.glob("result_*")):
        if not result_dir.is_dir():
            continue

        for mode_dir in sorted(child for child in result_dir.iterdir() if child.is_dir()):
            trace_files = sorted(mode_dir.glob("trace_*.json"))
            round_dir = mode_dir / "round_json"
            summary_file = mode_dir / "metrics" / "first_second_round_summary.json"
            comparison_file = mode_dir / "metrics" / "first_second_round_comparison.csv"

            if not trace_files and not round_dir.exists() and not summary_file.exists():
                continue

            trace_file = max(trace_files, key=lambda item: item.stat().st_mtime) if trace_files else None
            trace_data = _safe_json_load(trace_file) if trace_file else []
            if not isinstance(trace_data, list):
                trace_data = []

            round_files = sorted(round_dir.glob("round_*.json"), key=_round_number_from_path) if round_dir.exists() else []
            round_summaries: list[dict[str, Any]] = []
            for round_file in round_files:
                round_payload = _safe_json_load(round_file)
                if isinstance(round_payload, dict):
                    round_summaries.append(_round_summary(round_payload))

            summary_data = _safe_json_load(summary_file) or {}

            total_tokens = sum(_sum_token_round(item) for item in trace_data if isinstance(item, dict))
            final_accuracy = float(trace_data[-1].get("acc", 0.0)) if trace_data else 0.0
            average_similarity = (
                float(
                    sum(
                        _upper_triangle_average(item.get("sim_matrix", []))
                        for item in trace_data
                        if isinstance(item, dict)
                    )
                    / len(trace_data)
                )
                if trace_data
                else 0.0
            )

            question_preview = ""
            if round_summaries:
                question_preview = round_summaries[0]["question"].splitlines()[0][:180]

            run = {
                "experiment_id": _experiment_id(result_dir, mode_dir),
                "result_dir": result_dir.name,
                "mode": mode_dir.name,
                "path": str(mode_dir),
                "trace_path": str(trace_file) if trace_file else "",
                "summary_path": str(summary_file) if summary_file.exists() else "",
                "comparison_path": str(comparison_file) if comparison_file.exists() else "",
                "round_count": len(trace_data),
                "max_rounds": trace_data[-1].get("max_rounds", len(trace_data)) if trace_data else len(round_summaries),
                "final_accuracy": final_accuracy,
                "total_tokens": total_tokens,
                "average_similarity": average_similarity,
                "strategy_distribution": summary_data.get("strategy_distribution", {}),
                "question_preview": question_preview,
                "summary": summary_data,
                "latest_round": round_summaries[-1] if round_summaries else None,
                "rounds": round_summaries,
                "search_blob": " ".join(
                    [
                        result_dir.name,
                        mode_dir.name,
                        question_preview,
                        json.dumps(summary_data, ensure_ascii=False),
                        " ".join(item.get("question", "") for item in round_summaries),
                    ]
                ).lower(),
            }

            runs.append(run)

    runs.sort(key=lambda item: item["experiment_id"], reverse=True)
    return runs


def _experiment_detail(experiment_id: str) -> dict[str, Any]:
    experiment_dir = _resolve_experiment_dir(experiment_id)
    result_name, mode_name = experiment_id.split("__", 1)

    trace_files = sorted(experiment_dir.glob("trace_*.json"))
    trace_file = max(trace_files, key=lambda item: item.stat().st_mtime) if trace_files else None
    trace_data = _safe_json_load(trace_file) if trace_file else []
    if not isinstance(trace_data, list):
        trace_data = []

    summary_file = experiment_dir / "metrics" / "first_second_round_summary.json"
    summary_data = _safe_json_load(summary_file) or {}

    round_dir = experiment_dir / "round_json"
    round_files = sorted(round_dir.glob("round_*.json"), key=_round_number_from_path) if round_dir.exists() else []
    rounds: list[dict[str, Any]] = []
    for round_file in round_files:
        round_payload = _safe_json_load(round_file)
        if isinstance(round_payload, dict):
            rounds.append(_round_summary(round_payload))

    total_tokens = sum(_sum_token_round(item) for item in trace_data if isinstance(item, dict))

    return {
        "experiment_id": experiment_id,
        "result_dir": result_name,
        "mode": mode_name,
        "path": str(experiment_dir),
        "trace_path": str(trace_file) if trace_file else "",
        "summary_path": str(summary_file) if summary_file.exists() else "",
        "round_count": len(trace_data),
        "max_rounds": trace_data[-1].get("max_rounds", len(trace_data)) if trace_data else len(rounds),
        "final_accuracy": float(trace_data[-1].get("acc", 0.0)) if trace_data else 0.0,
        "total_tokens": total_tokens,
        "average_similarity": (
            float(
                sum(
                    _upper_triangle_average(item.get("sim_matrix", []))
                    for item in trace_data
                    if isinstance(item, dict)
                )
                / len(trace_data)
            )
            if trace_data
            else 0.0
        ),
        "strategy_distribution": summary_data.get("strategy_distribution", {}),
        "summary": summary_data,
        "trace": trace_data,
        "rounds": rounds,
        "latest_round": rounds[-1] if rounds else None,
    }


@app.get("/api/health")
def health_check() -> dict[str, Any]:
    return {"status": "ok", "experiment_root": str(EXP_ROOT)}


@app.get("/api/experiments")
def list_experiments(
    query: str | None = Query(default=None, description="Search in experiment metadata and round questions"),
    mode: str | None = Query(default=None, description="Filter by communication mode"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    runs = _scan_experiment_runs()

    if mode:
        runs = [item for item in runs if item["mode"].lower() == mode.lower()]

    if query:
        lowered = query.lower()
        runs = [item for item in runs if lowered in item.get("search_blob", "")]

    return {"items": runs[:limit], "total": len(runs)}


@app.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict[str, Any]:
    return _experiment_detail(experiment_id)


@app.get("/api/experiments/{experiment_id}/rounds")
def list_rounds(experiment_id: str) -> dict[str, Any]:
    detail = _experiment_detail(experiment_id)
    return {
        "experiment_id": detail["experiment_id"],
        "rounds": detail["rounds"],
        "summary": detail["summary"],
    }


@app.get("/api/experiments/{experiment_id}/rounds/{round_number}")
def get_round(experiment_id: str, round_number: int) -> dict[str, Any]:
    experiment_dir = _resolve_experiment_dir(experiment_id)
    round_file = experiment_dir / "round_json" / f"round_{round_number}.json"

    payload = _safe_json_load(round_file)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=404, detail="Round not found")

    return {
        "experiment_id": experiment_id,
        "round_number": round_number,
        "data": payload,
    }


@app.get("/api/experiments/{experiment_id}/search")
def search_rounds(experiment_id: str, query: str = Query(default="", min_length=1)) -> dict[str, Any]:
    detail = _experiment_detail(experiment_id)
    lowered = query.lower()
    matches = [
        item
        for item in detail["rounds"]
        if lowered in json.dumps(item, ensure_ascii=False).lower()
    ]
    return {"experiment_id": experiment_id, "query": query, "matches": matches}


@app.get("/api/experiments/{experiment_id}/artifact")
def download_artifact(experiment_id: str, relative_path: str) -> FileResponse:
    experiment_dir = _resolve_experiment_dir(experiment_id)
    target_path = (experiment_dir / relative_path).resolve()

    if experiment_dir.resolve() not in target_path.parents and target_path != experiment_dir.resolve():
        raise HTTPException(status_code=400, detail="Invalid artifact path")
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")

    return FileResponse(target_path)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        raw_data = await websocket.receive_text()
        config = json.loads(raw_data)
        nums_agents = config.get("nums_agents", 3)

        wf = LiveWorkflow(nums_agents=nums_agents)

        from PruneComm.data.dataset.mmlu_dataset import MMLUDataset
        val_dataset = MMLUDataset(split="val")
        total_steps = len(val_dataset)

        await websocket.send_json({
            "type": "task_config",
            "total": total_steps,
        })

        async for step_result in wf.run():
            round_start_time = time.time()

            for log in step_result["logs"]:
                await websocket.send_json({
                    "type": "agent_think",
                    **log,
                })
                await asyncio.sleep(0.01)

            duration = round(time.time() - round_start_time, 2)

            await websocket.send_json({
                "type": "step_analytics",
                "idx": step_result["idx"],
                "accuracy": step_result["accuracy"],
                "matrix": step_result["matrix"],
                "token_usage": step_result["token_usage"],
                "connections": step_result.get("ref_agent_dict", {}),
                "duration": duration,
                "sys_ans": step_result["sys_ans"],
                "correct_ans": step_result["correct_ans"],
            })

    except Exception as exc:
        print(f"WebSocket Error: {exc}")
        import traceback

        traceback.print_exc()
    finally:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)