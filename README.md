# Awesome Inference Engines

A curated, hardware-aware index of **LLM inference engines**, from general-purpose runtimes and high-throughput serving systems to deliberately specialized local engines that target one model family, one accelerator, or one memory bottleneck.

The emphasis is on **what executes the model**, how it uses compute and memory, and which workloads it is designed for. API servers, model managers, compilers, and research resources are included but identified separately. This is a map of the ecosystem, **not a performance ranking or an exhaustive inventory**.

## Contents

- [Find an engine by workload](#find-an-engine-by-workload)
- [Specialized and hardware-tuned engines](#specialized-and-hardware-tuned-engines)
- [Apple Silicon](#apple-silicon)
- [General-purpose local runtimes](#general-purpose-local-runtimes)
- [High-throughput and production inference](#high-throughput-and-production-inference)
- [Other runtimes and execution frameworks](#other-runtimes-and-execution-frameworks)
- [Servers, frontends, and orchestration](#servers-frontends-and-orchestration)
- [Benchmarks and discovery](#benchmarks-and-discovery)
- [How to compare engines](#how-to-compare-engines)
- [Contributing](#contributing)

## Find an engine by workload

| Situation | Good starting points | What to check |
| --- | --- | --- |
| CPU, mixed GPU hardware, GGUF | [llama.cpp](https://github.com/ggml-org/llama.cpp), [ik_llama.cpp](https://github.com/ikawrakow/ik_llama.cpp) | Quantization, GPU offload, context memory |
| Apple Silicon | [mlx-lm](https://github.com/ml-explore/mlx-lm), [oMLX](https://github.com/jundot/omlx), [Espetero](https://github.com/JarJarFran/espetero), [Kapitsa](https://github.com/nace-ai/kapitsa) | Supported model, unified memory, batch size, Metal/macOS version |
| NVIDIA consumer GPUs, compact quantized models | [ExLlamaV3](https://github.com/turboderp-org/exllamav3), [llama.cpp](https://github.com/ggml-org/llama.cpp) | Checkpoint format, CUDA/driver support, KV cache |
| Large MoE models that exceed VRAM | [Strata](https://github.com/Niko1221/Strata), [FreeToken](https://github.com/FlashML-org/FreeToken), [PolyStrata](https://github.com/simplexai-labs/PolyStrata), [Project Maya](https://github.com/mw00/project-maya) | Exact model, expert placement in VRAM/RAM/SSD, system RAM, storage latency |
| Specific NVIDIA Blackwell deployments | [Basalt](https://github.com/jesdga95/basalt), [NInfer](https://github.com/Neroued/ninfer), [Infernix](https://github.com/BarachielFallen/infernix) | GPU architecture and model restrictions |
| AMD Strix Halo | [Gufo](https://github.com/gufo-org/gufo), [llama.cpp](https://github.com/ggml-org/llama.cpp) | ROCm/driver support, shared-memory budget |
| Multiple concurrent requests / fleet serving | [vLLM](https://github.com/vllm-project/vllm), [SGLang](https://github.com/sgl-project/sglang), [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) | Prefill/decode throughput, batching, latency, multi-node operation |
| One-command local API | [Ollama](https://github.com/ollama/ollama), [LocalAI](https://github.com/mudler/LocalAI), [TabbyAPI](https://github.com/theroyallab/tabbyAPI) | Which inference backend is actually used |

These are discovery pointers, not endorsements or evidence that any particular model/hardware combination works. Consult each project's supported-model and platform documentation.

## Specialized and hardware-tuned engines

Purpose-built engines may trade model coverage or portability for a different speed/memory envelope. **A fork is listed separately when it makes substantive runtime changes**, with its lineage noted where known.

| Engine | Implementation / specialization | Primary focus |
| --- | --- | --- |
| [TensorFold](https://github.com/ashhart/TensorFold) | Native Zig engine with Metal, CUDA, and Vulkan paths | Direct local inference, speculative decoding, low-dependency serving |
| [Strata](https://github.com/Niko1221/Strata) | Heterogeneous GPU/CPU/SSD inference | Large MoE models, tiered expert storage, local API |
| [Basalt](https://github.com/jesdga95/basalt) | Blackwell-focused local engine | Qwen/DeepSeek model paths, GPU plus host-memory expert placement |
| [Project Maya](https://github.com/mw00/project-maya) | Strata-derived, model-specialized engine | Large GLM, DeepSeek, MiniMax-family MoE inference; multi-GPU configurations |
| [PolyStrata](https://github.com/simplexai-labs/PolyStrata) | Strata engine plus separately developed model backends | Broader model-family support on consumer hardware |
| [FreeToken](https://github.com/FlashML-org/FreeToken) | Edge-oriented heterogeneous MoE runtime | CPU/GPU co-execution, expert caching, elastic memory |
| [NInfer](https://github.com/Neroued/ninfer) | C++/CUDA engine | Selected models on RTX 5090 and DGX Spark, including multi-device configurations |
| [Infernix](https://github.com/BarachielFallen/infernix) | NInfer-derived CUDA engine | Qwen-family inference on RTX 50-series, host expert offload |
| [Gufo](https://github.com/gufo-org/gufo) | Hardware-specific engine for AMD Strix Halo | Ryzen AI MAX / Radeon 8060S, multiple model modalities |
| [Xolotl](https://github.com/Indras-Mirror/Xolotl) | Strata-derived engine with additional model backends | Large MoE models on consumer NVIDIA GPUs |
| [Avalon](https://github.com/freriadoc/Avalon) | llama.cpp-derived engine | Qwen3.8-Flash-Next with expert caching; especially AMD/ROCm tuning |
| [Sync-Strata](https://github.com/hiruhiru2005/sync-strata) | Strata fork and custom quantizations | Qwen3.8-Flash-Next on consumer PCs |
| [Speedy](https://github.com/DevDock-AI/Speedy) | Strata-derived engine | Consumer-NVIDIA MoE inference and coding-agent workloads; **personal/non-commercial license** |
| [YASAKANI](https://github.com/yasakani-dev/yasakani) | Model-specific CUDA engine | Qwen3.8-27B on Windows/NVIDIA RTX; other models are experimental |
| [yasaheni](https://github.com/sahenjp/yasaheni) | Linux/GGUF-oriented port of YASAKANI | Broader build targets and model input on Linux |

## Apple Silicon

| Project | What it is | Focus |
| --- | --- | --- |
| [Espetero](https://github.com/JarJarFran/espetero) | Native C++/Metal inference engine | Concurrent text, vision, and classification inference on Macs |
| [Kapitsa](https://github.com/nace-ai/kapitsa) | Apple Silicon-specific inference engine | Local coding-agent models and tuned Metal execution |
| [raceline](https://github.com/audenvenn/raceline) | Purpose-built native agent/inference runtime | Qwen-family optimization on individual Macs; **research/maintenance mode** |
| [TurboFieldfare](https://github.com/drumih/turbo-fieldfare) | Swift/Metal, model-specific runtime | SSD-streamed Gemma 4 MoE inference under a small RAM budget |
| [oMLX](https://github.com/jundot/omlx) | MLX-based inference server | Continuous batching, persistent/tiered KV cache, Mac management UI |
| [mlx-lm](https://github.com/ml-explore/mlx-lm) | LLM inference and fine-tuning on MLX | General MLX language-model inference |
| [mlx-vlm](https://github.com/Neywa-Labs/mlx-vlm) | MLX vision-language inference toolkit | Multimodal models and image inputs |
| [MLX](https://github.com/ml-explore/mlx) | **Array framework, not a standalone LLM server** | Apple Silicon compute foundation for multiple engines above |

## General-purpose local runtimes

| Project | What it does | Distinction |
| --- | --- | --- |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Portable C/C++ inference with GGUF | Broad CPU/GPU and quantized-model support |
| [ik_llama.cpp](https://github.com/ikawrakow/ik_llama.cpp) | Optimized llama.cpp fork | CPU/hybrid execution and additional quantization work |
| [ExLlamaV3](https://github.com/turboderp-org/exllamav3) | Quantized inference library | EXL3, parallel inference, consumer GPU deployment |
| [ExLlamaV2](https://github.com/turboderp-org/exllamav2) | Quantized inference library | EXL2 and earlier ExLlama generation; useful for existing model artifacts |
| [mistral.rs](https://github.com/EricLBuehler/mistral.rs) | Rust inference runtime | Local accelerated, quantized, and multimodal inference |
| [MLC-LLM](https://github.com/mlc-ai/mlc-llm) | Compiled deployment/runtime stack | Cross-platform model compilation and deployment |
| [PowerInfer](https://github.com/Tiiny-AI/PowerInfer) | Heterogeneous inference runtime | Local LLM execution using CPU/GPU cooperation |
| [BitNet](https://github.com/microsoft/BitNet) | Specialized inference framework | 1-bit / low-bit BitNet models, not a generic arbitrary-weight runtime |

## High-throughput and production inference

| Project | Focus | Notes |
| --- | --- | --- |
| [vLLM](https://github.com/vllm-project/vllm) | High-throughput LLM serving | Continuous batching, paged KV-cache management |
| [SGLang](https://github.com/sgl-project/sglang) | Efficient model serving and structured generation | Agent/tool workloads, caching, batching |
| [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) | NVIDIA-optimized model execution | GPU kernels, quantization, distributed serving |
| [LMDeploy](https://github.com/InternLM/lmdeploy) | LLM serving/deployment toolkit | TurboMind and deployment tooling |
| [Sonar](https://github.com/dphnAI/sonar) | vLLM-derived inference engine | Formerly **Aphrodite Engine**; follow the current repository |
| [LightLLM](https://github.com/ModelTC/LightLLM) | LLM serving | High-performance inference with dynamic scheduling |
| [FastDeploy](https://github.com/PaddlePaddle/FastDeploy) | Paddle ecosystem inference/serving | Model serving and high-performance backend paths |
| [vLLM-Omni](https://github.com/vllm-project/vllm-omni) | Multimodal model serving | Omni-modal inference capabilities in the vLLM ecosystem |
| [Text Generation Inference (TGI)](https://github.com/huggingface/text-generation-inference) | Hugging Face generation server | **Maintenance mode** according to the repository README |

## Other runtimes and execution frameworks

| Project | Role | Scope |
| --- | --- | --- |
| [CTranslate2](https://github.com/OpenNMT/CTranslate2) | Inference runtime | Optimized Transformer inference, including translation and speech workloads |
| [OpenVINO GenAI](https://github.com/openvinotoolkit/openvino.genai) | Runtime API / model-serving library | Intel-oriented generative AI execution |
| [Candle](https://github.com/huggingface/candle) | Rust ML framework and inference library | Lightweight local inference, model implementations |
| [WebLLM](https://github.com/mlc-ai/web-llm) | Browser runtime | WebGPU-based in-browser LLM inference |

## Servers, frontends, and orchestration

These projects are useful parts of inference deployment, but **a user-facing API or scheduler is not necessarily an independent execution engine**.

| Project | Role | Runtime relationship |
| --- | --- | --- |
| [Ollama](https://github.com/ollama/ollama) | Local model manager and inference server | Bundles/uses model execution backends, notably llama.cpp lineage |
| [KoboldCpp](https://github.com/LostRuins/koboldcpp) | Integrated local server/runtime | llama.cpp-derived with story/roleplay-oriented UI and features |
| [LocalAI](https://github.com/mudler/LocalAI) | Multi-backend self-hosted API | Runs models via interchangeable engines |
| [TabbyAPI](https://github.com/theroyallab/tabbyAPI) | API serving frontend | Recommended server for ExLlamaV3 |
| [llama-swap](https://github.com/mostlygeek/llama-swap) | Local multi-model proxy | Starts/switches backend model servers, rather than computing inference itself |
| [Triton Inference Server](https://github.com/triton-inference-server/server) | Production serving infrastructure | Multiple model backends; distinct from TensorRT-LLM |
| [Dynamo](https://github.com/ai-dynamo/dynamo) | Distributed inference infrastructure | Orchestration and optimization around serving backends |
| [llm-d](https://github.com/llm-d/llm-d) | Distributed LLM serving platform | Kubernetes-native serving architecture |
| [Ray Serve](https://github.com/ray-project/ray) | Distributed application serving | Serving/orchestration, usually delegates actual token computation |

## Benchmarks and discovery

- [llamaperf.com/engine](https://llamaperf.com/engine) — Community engine results; examine the hardware, model, quantization, and methodology behind each measurement.
- [Awesome LLM Inference Engine](https://github.com/sihyeong/Awesome-LLM-Inference-Engine) — Broader engine taxonomy and research survey.
- [awesome-local-llm](https://github.com/rafska/awesome-local-llm) — Local LLM platforms, engines, and ecosystem tools.
- [awesome-local-ai](https://github.com/janhq/awesome-local-ai) — Wider local AI ecosystem.
- [awesome-local-llms](https://github.com/vince-lam/awesome-local-llms) and [llmrepos.com](https://llmrepos.com) — Repo discovery and ecosystem tracking.
- [awesome-inference-specialization](https://github.com/SJTU-iBDS-Lab/awesome-inference-specialization) — Research-oriented specialized execution systems.
- [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/) — Early announcements and community experiments; verify claims against upstream source and reproducible measurements.

## How to compare engines

**Tokens per second in isolation is not a sufficient comparison.** Before interpreting a result, record:

1. **Model and exact artifact:** architecture, revision, quantization, tokenizer, and draft/MTP weights.
2. **Hardware:** accelerator, memory size and bandwidth, CPU, RAM, PCIe/interconnect, SSD, drivers, and operating system.
3. **Workload:** prompt and generated-token lengths, filled context, modality, batch/concurrency, cache warmth, and whether tool/structured outputs work.
4. **Measurements:** prefill throughput, decode throughput, time to first token, end-to-end task completion time, memory footprint, and energy when available.
5. **Correctness:** equivalent generated outputs under controlled decoding, tool-call validity, long-context retrieval, and quality changes from approximation or altered quantization.
6. **Reproducibility:** executable command, engine commit/release, artifacts, warmup protocol, sample size, variance, and raw results.

Be especially cautious when a specialized engine claims to beat a general one: the comparison may change the model artifact, attention implementation, prompt length, speculative decoding, batch size, or cache state. Independent results and clearly stated limitations are more valuable than headline speeds.

## Contributing

Open a pull request with the project URL, a one-sentence explanation of **what executes inference**, supported hardware/model families, and a pointer to a runnable example or technical documentation. If the project is a fork, identify its upstream. If it is a wrapper or infrastructure layer, put it in the corresponding section.

Prefer the upstream source over social posts. Avoid unverified speed claims, duplicated names, dead repositories, star counts, and entries that are only mockups or future announcements. Experimental projects are welcome when their scope and limitations are clear.

This list has no affiliation with the projects linked above. Hardware/model support, licenses, maintenance, and performance can change; consult each upstream project before deployment.
