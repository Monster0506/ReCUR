import argparse
import asyncio
import json
from pathlib import Path
from random import shuffle
from typing import List, Dict, Any, Tuple

from agents.alternative_responder import AlternativeResponder
from agents.base_responder import BaseResponder
from agents.final_selector import FinalSelector
from agents.round_counter import heuristic_rounds
from core.llm import GoogleGenaiLLM, EchoLLM
from core.utils import configure_logging, load_config
from core.models import Response
from core.context import load_file_fragments
from graders.rubric_grader import RubricGrader


# --------------------------------------------------------------------------- #
# LLM factory
# --------------------------------------------------------------------------- #
def build_llm(cfg: Dict[str, Any], use_echo: bool = False):
    if use_echo:
        return EchoLLM()
    return GoogleGenaiLLM(
        model=cfg.get("model", "gemini-2.0-flash-001"),
        api_key=cfg.get("api_key"),
        fragments=cfg.get("fragments"),
    )


# --------------------------------------------------------------------------- #
# Pipeline — now returns *both* the winning answer and the full response list
# --------------------------------------------------------------------------- #
async def pipeline(cfg: Dict[str, Any]) -> Tuple[Response, List[Response]]:
    """
    Run the full ReCUR loop and return

        (final_best_response, list_of_every_response_with_scores)

    All scoring happens *inside* this function so every Response object
    carries a non‑zero `score`.
    """
    # build components
    llm = build_llm(cfg, use_echo=cfg.get("echo", False))
    temp = cfg.get("temperature", 0.4)
    grader = RubricGrader(llm=llm)
    selector = FinalSelector(grader)
    prompt: str = cfg["prompt"]

    # helpers --------------------------------------------------------------
    async def score_response(resp: Response) -> None:
        resp.score = await grader.score(resp.text, prompt)

    async def score_many(resps: List[Response]) -> None:
        await asyncio.gather(*(score_response(r) for r in resps))

    # Step 1 – base answer --------------------------------------------------
    base_resp = await BaseResponder(llm, temp)(prompt)
    await score_response(base_resp)
    current_best: Response = base_resp
    all_responses: List[Response] = [base_resp]

    # Steps 2‑3 – recursive improvement ------------------------------------
    rounds = cfg.get("rounds") or heuristic_rounds(prompt)
    alts_per_round = cfg.get("alts", 3)

    for i in range(rounds):
        print(f"Beginning round {i+1} of {rounds}...")
        # generate alternatives in parallel
        alt_tasks = [
            AlternativeResponder(llm, temp).generate(prompt, current_best.text, idx=i)
            for i in range(alts_per_round)
        ]
        alternatives: List[Response] = await asyncio.gather(*alt_tasks)

        # score them (parallel)
        await score_many(alternatives)

        # keep the best so far
        best_alt = max(alternatives, key=lambda r: r.score)
        if best_alt.score > current_best.score:
            current_best = best_alt

        all_responses.extend(alternatives)

    # Step 4 – final shuffle + re‑select (scores already present) ----------
    shuffle(all_responses)  # cosmetic only
    final_best = await selector.select(all_responses)

    # Step 5 – return -------------------------------------------------------
    return final_best, all_responses


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def run_cli() -> None:  # pragma: no cover
    # ───────────────────────────────────────────────────────── Parser
    parser = argparse.ArgumentParser(
        prog="recur",
        description="Recursive-Cognition-Upgrade-Routine (ReCUR) pipeline",
    )

    parser.add_argument(
        "-p",
        "--prompt",
        help="User prompt that the ReCUR pipeline will answer",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        metavar="YAML",
        help="Path to a YAML config file (defaults to config/default.yaml)",
    )
    parser.add_argument(
        "-b",
        "--rubric-file",
        type=Path,
        metavar="FILE",
        help="Optional grading rubric file (overrides built‑in rubric)",
    )
    parser.add_argument(
        "-n",
        "--rounds",
        type=int,
        metavar="INT",
        help="Force an exact number of refinement rounds (otherwise heuristic)",
    )
    parser.add_argument(
        "-a",
        "--alts",
        type=int,
        metavar="INT",
        help="Number of alternatives generated in parallel each round (default 3)",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        metavar="FLOAT",
        help="Sampling temperature for all LLM calls (default 0.4)",
    )
    parser.add_argument(
        "-l",
        "--logfile",
        type=Path,
        metavar="PATH",
        help="Write JSON log lines to this file instead of stderr",
    )
    parser.add_argument(
        "-L",
        "--log-level",
        type=str,
        metavar="LEVEL",
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR)",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        metavar="PATH",
        help="Write the *final* answer text to PATH",
    )
    parser.add_argument(
        "-j",
        "--audit-json",
        type=Path,
        metavar="PATH",
        help="Write a JSON file containing every response and its score",
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Use the stub Echo LLM instead of calling Google GenAI (for dry‑runs)",
    )
    parser.add_argument(
        "-f",
        "--context-file",
        action="append",
        type=Path,
        metavar="PATH",
        help="Path(s) to text file(s) whose contents should be included as context",
    )

    args = parser.parse_args()

    # ───────────────────────────────────────────────────────── Config merge
    # 1. load YAML (default or user‑supplied)
    default_cfg_path = Path(__file__).parent.parent / "config" / "default.yaml"
    yaml_cfg = load_config(args.config or default_cfg_path, overrides=None)
    print(yaml_cfg)

    # 2. build dict of CLI overrides where the user actually typed a value
    cli_overrides = {
        key: value
        for key, value in vars(args).items()
        if value is not None and key != "config"
    }
    print(cli_overrides)

    # 3. final merged cfg  (YAML first, CLI wins)
    cfg: Dict[str, Any] = {**yaml_cfg, **cli_overrides}
    print(cfg)

    # 4. sanity check
    if "prompt" not in cfg or not cfg["prompt"]:
        parser.error(
            "A prompt is required (give -p/--prompt or set it in the YAML config)"
        )

    # ───────────────────────────────────────────────────────── Logging
    configure_logging(
        cfg.get("logfile"),
        cfg.get("log_level", "INFO"),
    )

    # 5. Context fragments
    cfg["fragments"] = load_file_fragments(cfg.get("context_file", []))

    # ───────────────────────────────────────────────────────── Run pipeline
    final, all_responses = asyncio.run(pipeline(cfg))

    # stdout → only winning answer
    print(final.text)

    # ───────────────────────────────────────────────────────── Artifacts
    if cfg.get("audit_json"):
        chronicle = [
            {
                "agent": r.provenance.get("agent", "unknown"),
                "score": r.score,
                "text": r.text,
            }
            for r in all_responses
        ]
        chronicle.append({"agent": "final", "score": final.score, "text": final.text})
        Path(cfg["audit_json"]).write_text(
            json.dumps({"prompt": cfg["prompt"], "chronicle": chronicle}, indent=2),
            encoding="utf-8",
        )

    if cfg.get("output_file"):
        Path(cfg["output_file"]).write_text(final.text, encoding="utf-8")
