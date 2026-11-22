# Local inference benchmark probe

This small, dependency-free Python probe measures **streaming chat responses** from OpenAI-compatible inference endpoints. It produces a machine-readable JSON receipt with raw per-run observations. It is a starting point for reproducible experiments, **not** a published cross-engine leaderboard.

## Run

Start your engine and load a known model. Then run with Python 3.9 or newer:

```bash
python3 bench/probe.py \
  --base-url http://127.0.0.1:8000 \
  --model YOUR_EXACT_MODEL_ID \
  --engine 'ENGINE_NAME AND VERSION' \
  --hardware 'GPU, VRAM, CPU, RAM, OS, DRIVER' \
  --runs 5 --warmups 2 \
  --output receipt.json
```

The probe uses `POST /v1/chat/completions` with `stream: true`, `temperature: 0`, and a 128-token generation cap. The `--base-url` can already end in `/v1`. It runs two deterministic prompts:

- `short`: an exact-answer one-word response, for short-request latency.
- `needle`: a longer input with a planted answer and an exact-answer check. Default target size is approximately 8,192 **characters**, not tokens.

Use `--case short` or `--case needle` to select one. Set `--target-chars 32768` to change the needle input length and `--max-tokens` to adjust the output cap. Actual prompt token counts depend on the model tokenizer and are only known when the server reports them.

If your server rejects `stream_options`, add `--no-usage-request` and expect missing token counts and token-rate estimates. For an authenticated server, set `BENCH_API_KEY` in the environment; the key and endpoint address are excluded from the receipt. Non-loopback endpoints require explicit `--allow-remote`: **that sends the test prompts to the remote host**.

## Reading the receipt

| Field | Meaning | Caveat |
| --- | --- | --- |
| `elapsed_ms` | Wall-clock time from HTTP request start through stream completion | Includes local connection/server overhead |
| `ttft_visible_ms` | Time to first nonempty user-visible text delta | Not model-internal prefill latency; null if no visible text |
| `prompt_tokens_reported`, `completion_tokens_reported` | Server-provided token counts | Null when missing; server accounting varies |
| `post_first_visible_rate_approx_tok_s` | Reported completion tokens divided by time from first visible delta to stream end | **Approximation**, not pure decode throughput; can include hidden reasoning tokens and finalization |
| `exact_answer` | Exact match to expected word after whitespace/case normalization | A sanity check, not comprehensive model-quality evaluation |
| `summary` | Median and nearest-rank p95 across measured runs | Small samples make p95 unstable; raw trials are the evidence |

The receipt stores the prompt's SHA-256, prompt character length, result hash, measured timings, and declared hardware/engine/model, but not raw prompts or raw model output. Warmup requests are not included in the measured samples.

## Comparing engines responsibly

Use the **same actual model weights and quantization**, output limit, prompt cases, context size, sampling parameters, server state, and concurrency. Report exact model checkpoint and artifact hash, runtime commit or release, GPU/CPU and memory capacity, drivers, operating system, power limits, cache-warmness, and any offload settings alongside receipts. A matching model name alone is insufficient.

Runs on different machines or models are useful observations but not direct speed comparisons. The probe sends one request at a time; it does **not** measure multi-user throughput, memory peaks, joules per token, long-run stability, or quality beyond the two answer checks. An engine that lacks this HTTP streaming protocol needs its own adapter; do not invent missing measurements.

Offline protocol tests:

```bash
python3 -m unittest discover -s bench -p 'test_*.py' -v
```

For upstream-documented engine constraints, see the [compatibility matrix](../compatibility.md).
