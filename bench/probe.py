#!/usr/bin/env python3
"""Small, dependency-free probe for OpenAI-compatible streaming chat endpoints."""

import argparse
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SCHEMA = "awesome-inference-engines/probe-1"


def make_case(name, target_chars):
    if name == "short":
        prompt = "Reply with exactly the single lowercase word cedar. No punctuation or explanation."
        return {"name": name, "prompt": prompt, "expected": "cedar"}
    if name == "needle":
        if target_chars < 1024:
            raise ValueError("--target-chars must be at least 1024 for the needle case")
        rng = random.Random(20261122)
        words = ("maple", "quartz", "river", "copper", "lantern", "violet", "forest", "orbit")
        prefix = (
            "Read the reference text. At the end, reply only with the lowercase word "
            "on the line that starts UNIQUE_CHECKWORD. Ignore all other words.\n\n"
        )
        suffix = "\n\nWhat is the UNIQUE_CHECKWORD? Reply with one word."
        filler = []
        filler_chars = 0
        filler_target = target_chars - len(prefix) - len(suffix) - 50
        while filler_chars < filler_target:
            word = words[rng.randrange(len(words))]
            filler.append(word)
            filler_chars += len(word) + 1
        boundary = len(filler) * 3 // 4
        filler.insert(boundary, "\nUNIQUE_CHECKWORD: saturn\n")
        prompt = prefix + " ".join(filler) + suffix
        return {"name": name, "prompt": prompt, "expected": "saturn"}
    raise ValueError(f"Unknown case: {name}")


def endpoint_url(base_url, allow_remote):
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("--base-url must be an http(s) URL with a hostname")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Do not put credentials, query parameters, or fragments in --base-url")
    if not allow_remote and parsed.hostname.lower() not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Only loopback hosts are allowed by default; use --allow-remote explicitly")
    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        return root + "/chat/completions"
    return root + "/v1/chat/completions"


def stream_chunks(response):
    """Yield parsed JSON data from server-sent events, ignoring non-data fields."""
    data_lines = []
    for raw in response:
        line = raw.decode("utf-8").rstrip("\r\n")
        if not line:
            if data_lines:
                data = "\n".join(data_lines)
                data_lines = []
                if data == "[DONE]":
                    return
                yield json.loads(data)
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip(" "))
    if data_lines:
        data = "\n".join(data_lines)
        if data != "[DONE]":
            yield json.loads(data)


def trial(url, model, case, max_tokens, timeout, request_usage, api_key):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": case["prompt"]}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if request_usage:
        payload["stream_options"] = {"include_usage": True}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    began = time.perf_counter()
    first_visible = None
    output = []
    usage = {}
    finish_reason = None
    try:
        with urlopen(req, timeout=timeout) as response:
            for chunk in stream_chunks(response):
                if isinstance(chunk.get("usage"), dict):
                    usage = chunk["usage"]
                for choice in chunk.get("choices") or []:
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        if first_visible is None:
                            first_visible = time.perf_counter()
                        output.append(content)
                    if choice.get("finish_reason") is not None:
                        finish_reason = choice["finish_reason"]
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} from chat endpoint") from exc
    except URLError as exc:
        raise RuntimeError(f"Connection to chat endpoint failed: {exc.reason}") from exc
    ended = time.perf_counter()
    answer = "".join(output)
    completion_tokens = usage.get("completion_tokens")
    output_window = (ended - first_visible) if first_visible is not None else None
    rate = None
    if isinstance(completion_tokens, int) and completion_tokens > 0 and output_window and output_window > 0:
        rate = round(completion_tokens / output_window, 2)
    return {
        "elapsed_ms": round((ended - began) * 1000, 2),
        "ttft_visible_ms": round((first_visible - began) * 1000, 2) if first_visible is not None else None,
        "output_chars": len(answer),
        "output_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "prompt_tokens_reported": usage.get("prompt_tokens"),
        "completion_tokens_reported": completion_tokens,
        "post_first_visible_rate_approx_tok_s": rate,
        "exact_answer": answer.strip().lower() == case["expected"],
        "finish_reason": finish_reason,
    }


def summarize(samples):
    def stats(field):
        values = sorted(v[field] for v in samples if isinstance(v[field], (int, float)))
        if not values:
            return None
        return {
            "median": round(statistics.median(values), 2),
            "p95_nearest_rank": round(values[math.ceil(len(values) * 0.95) - 1], 2),
            "sample_count": len(values),
        }

    return {
        "exact_answers": sum(1 for v in samples if v["exact_answer"]),
        "sample_count": len(samples),
        "elapsed_ms": stats("elapsed_ms"),
        "ttft_visible_ms": stats("ttft_visible_ms"),
        "post_first_visible_rate_approx_tok_s": stats("post_first_visible_rate_approx_tok_s"),
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Server origin, optionally ending in /v1")
    parser.add_argument("--model", required=True, help="Exact model identifier served by the endpoint")
    parser.add_argument("--engine", required=True, help="Engine name and version, as observed")
    parser.add_argument("--hardware", required=True, help="GPU/CPU, VRAM/RAM, and relevant environment")
    parser.add_argument("--case", choices=("short", "needle"), action="append", dest="cases")
    parser.add_argument("--target-chars", type=int, default=8192, help="Approximate character size for needle input (not tokens)")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--runs", type=int, default=3, help="Measured runs per case")
    parser.add_argument("--warmups", type=int, default=1, help="Unreported warmups per case")
    parser.add_argument("--timeout", type=float, default=120, help="Per-request socket timeout in seconds")
    parser.add_argument("--no-usage-request", action="store_true", help="Omit stream_options for incompatible engines")
    parser.add_argument("--allow-remote", action="store_true", help="Opt in to sending prompts to a non-loopback endpoint")
    parser.add_argument("--output", default="-", help="Receipt JSON path, or - for stdout")
    return parser


def run(args):
    if args.runs < 1 or args.warmups < 0 or args.max_tokens < 1 or args.timeout <= 0:
        raise ValueError("--runs and --max-tokens must be positive; --warmups nonnegative; --timeout positive")
    url = endpoint_url(args.base_url, args.allow_remote)
    cases = [make_case(name, args.target_chars) for name in dict.fromkeys(args.cases or ["short", "needle"])]
    receipt = {
        "schema": SCHEMA,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "engine": args.engine,
        "model": args.model,
        "hardware": args.hardware,
        "settings": {
            "max_tokens": args.max_tokens,
            "temperature": 0,
            "stream": True,
            "stream_usage_requested": not args.no_usage_request,
            "runs": args.runs,
            "warmups": args.warmups,
            "target_chars": args.target_chars,
        },
        "cases": [],
    }
    for case in cases:
        print(f"Probing {case['name']} ({args.warmups} warmup, {args.runs} measured)...", file=sys.stderr)
        for _ in range(args.warmups):
            trial(url, args.model, case, args.max_tokens, args.timeout,
                  not args.no_usage_request, os.environ.get("BENCH_API_KEY"))
        samples = []
        for _ in range(args.runs):
            samples.append(trial(url, args.model, case, args.max_tokens, args.timeout,
                                 not args.no_usage_request, os.environ.get("BENCH_API_KEY")))
        receipt["cases"].append({
            "case": case["name"],
            "prompt_chars": len(case["prompt"]),
            "prompt_sha256": hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest(),
            "expected_answer": case["expected"],
            "trials": samples,
            "summary": summarize(samples),
        })
    return receipt


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        receipt = run(args)
        encoded = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
        if args.output == "-":
            sys.stdout.write(encoded)
        else:
            with open(args.output, "w", encoding="utf-8") as output:
                output.write(encoded)
    except (ValueError, RuntimeError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Probe failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
