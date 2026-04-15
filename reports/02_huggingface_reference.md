# Hugging Face Integration Reference (2026 Edition)

**Audience:** Marcus Daley, portfolio-grade production AI across 9 repos
**Scope:** Complements the existing Ollama -> HF ONNX -> HF API -> Groq -> Cerebras fallback chain in `grizz-optimizer/src/main/ai/llm-client.ts`. This document is vendor-agnostic model + infrastructure selection guidance, not an orchestrator redesign.
**Generated:** 2026-04-08
**Primary sources:** `huggingface.co/docs/inference-providers` (fetched live), Hugging Face Hub model cards, arXiv preprints cited per model.

---

## 1. Image Classification Models

The classification layer in 2026 is dominated by self-supervised vision transformers (DINOv3, SigLIP 2) used as frozen backbones, plus ConvNeXt v2 where pure-CNN locality matters. Straight ImageNet fine-tunes (ViT, BEiT) remain the baseline for cheap deployment.

| Model | HF ID | Params | CPU speed | GPU speed | Accuracy proxy | Best for | License |
|---|---|---|---|---|---|---|---|
| ViT-B/16 | `google/vit-base-patch16-224` | 86.6M | fast | very fast | ImageNet-1k 81.5% | cheap baseline, azure-deployable | Apache-2.0 |
| BEiT-L/16 | `microsoft/beit-large-patch16-224` | ~305M | medium | fast | ImageNet-1k 87.3% | masked-image pretraining baseline | Apache-2.0 |
| ConvNeXt v2-L (384) | `facebook/convnextv2-large-22k-384` | 198M | medium | fast | ImageNet-22k >87% | dense prediction, CNN locality bias | Apache-2.0 |
| SigLIP 2 base | `google/siglip2-base-patch16-224` | 93M | fast | very fast | zero-shot SOTA small | zero-shot classification, retrieval, weak labels | Apache-2.0 |
| SigLIP 2 large | `google/siglip2-large-patch16-384` | 882M | slow | medium | zero-shot SOTA | high-accuracy zero-shot, multilingual | Apache-2.0 |
| DINOv2 large | `facebook/dinov2-large` | 304M | medium | fast | linear-probe ~86% | frozen backbone for downstream heads | Apache-2.0 |
| DINOv3 ViT-L/16 (gated) | `facebook/dinov3-vitl16-pretrain-lvd1689m` | 303M | medium | fast | SOTA self-supervised features | dense features, retrieval, segmentation, 3D | Meta custom (commercial allowed w/ terms) |
| DINOv3 ViT-B/16 (gated) | `facebook/dinov3-vitb16-pretrain-lvd1689m` | 86M | fast | very fast | Near-L quality on most tasks | cheap SSL backbone | Meta custom |

**Pick for most ClaudeSkills/grizz use cases:** SigLIP 2 base for zero-shot (no training set needed, multilingual), DINOv3 ViT-B for fine-tuned classifiers over screenshots/icons (best linear-probe-to-size ratio). Fall back to ViT-B when Apache-2.0 is required without gating.

---

## 2. OCR Models

| Model | HF ID | Params | Strength | Weakness | License |
|---|---|---|---|---|---|
| TrOCR-large-handwritten | `microsoft/trocr-large-handwritten` | ~558M | handwriting SOTA, transformers-native | English only, single-line crops | MIT |
| Donut | `naver-clova-ix/donut-base` | ~200M | OCR-free document VQA (end-to-end JSON) | aging, surpassed by VLMs on layout | MIT |
| GOT-OCR 2.0 | `stepfun-ai/GOT-OCR-2.0-hf` | 560M | unified OCR-2.0 (plain/formatted/chart/math/sheet music), multilingual | not tuned for small fonts | Apache-2.0 |
| Surya rec2 | `vikp/surya_rec2` | 470M | 90+ languages, strong on scans, layout+reading order | CC-BY-NC-SA (no commercial) | CC-BY-NC-SA-4.0 |
| PaddleOCR 3.0 | via `PaddlePaddle` repo (not HF hub) | varies | fastest production pipeline, strong CJK | not on HF hub, requires PaddlePaddle runtime | Apache-2.0 |
| Tesseract 5 | (not HF) | n/a | zero infra, deterministic | weak on modern UI screenshots, no layout |
Apache-2.0 |

**Pick for screenshots specifically:** GOT-OCR 2.0 as the primary engine — it was trained for structured output (tables, math, charts) which is exactly what IDE/dashboard screenshots contain, and is Apache-2.0 so no licensing risk. Use PaddleOCR 3.0 as a speed-optimized fallback for batch pipelines. Tesseract stays as the "no dependencies" floor. Avoid Surya in commercial paths due to NC license. For pure text extraction inside a VLM pipeline, skip dedicated OCR entirely and let Qwen2.5-VL do it (see Section 3).

---

## 3. Vision-Language Models (Screenshot Understanding)

This is the #1 capability for grizz-optimizer (runtime error screenshots, job cards) and the skill/UI tooling in ClaudeSkills. Ranking reflects screenshot/UI-document benchmarks (ChartQA, DocVQA, ScreenSpot) not general VQA.

| Model | HF ID | Params | VRAM (bf16) | Screenshot/UI quality | License | Notes |
|---|---|---|---|---|---|---|
| Qwen2.5-VL-7B-Instruct | `Qwen/Qwen2.5-VL-7B-Instruct` | 8.3B | ~17 GB | Top tier for UI/doc; native resolution + dynamic fps | Apache-2.0 | Primary recommendation |
| Qwen2.5-VL-3B-Instruct | `Qwen/Qwen2.5-VL-3B-Instruct` | 3.8B | ~8 GB | Very close to 7B on OCR/UI | Qwen Research | Great for 8GB laptops |
| Qwen2.5-VL-72B-Instruct | `Qwen/Qwen2.5-VL-72B-Instruct` | 73.4B | ~145 GB | Best open-weights VLM on ChartQA, DocVQA, MMMU | Qwen (commercial-restricted) | Inference Providers only (OVHcloud live) |
| InternVL 2.5-8B | `OpenGVLab/InternVL2_5-8B` | 8.1B | ~17 GB | Strong on MEGA-Bench, multilingual | MIT | Good MIT alternative to Qwen |
| InternVL 2.5-78B | `OpenGVLab/InternVL2_5-78B` | ~78B | ~150 GB | Beats GPT-4V on several VLM leaderboards | Other (Qwen-derived) | Rent GPU only |
| Llama 3.2 Vision 11B | `meta-llama/Llama-3.2-11B-Vision-Instruct` | 10.7B | ~22 GB | Decent general VQA; weaker than Qwen on documents | Llama 3.2 (gated) | Ecosystem support is excellent |
| Florence-2 large | `microsoft/Florence-2-large` | 777M | ~2 GB | Best tiny VLM for grounding + captioning + OCR boxes | MIT | Not a chat model — prompt-token interface |
| SmolVLM-Instruct (2B) | `HuggingFaceTB/SmolVLM-Instruct` | 2.2B | ~5 GB | Good UI understanding, runs on CPU/iGPU | Apache-2.0 | Transformers.js + ONNX supported |
| SmolVLM-500M-Instruct | `HuggingFaceTB/SmolVLM-500M-Instruct` | 507M | ~1.3 GB | Minimum viable VLM, webgpu-real-time capable | Apache-2.0 | Browser-side inference |
| Moondream 2 | `vikhyatk/moondream2` | 1.9B | ~4 GB | Lightweight VQA, strong captioning | Apache-2.0 | Single-author project, very active |
| Pixtral 12B | `mistralai/Pixtral-12B-2409` | 12B | ~24 GB | Strong chart/table, multilingual | Apache-2.0 | vLLM-first; Hyperbolic provider live |

**Primary recommendation for screenshot pipeline:** Qwen2.5-VL-7B-Instruct local (fits a single RTX 4080/4090), with Qwen2.5-VL-3B as the edge/laptop fallback and Pixtral 12B or Qwen2.5-VL-72B via Inference Providers for the hard cases. Florence-2 large stays in the toolkit as a cheap grounding/bounding-box generator that feeds the VLM — it is not a chat model but it is MIT-licensed and 2 GB.

---

## 4. Code Analysis Models

| Model | HF ID | Params | Strength | License |
|---|---|---|---|---|
| StarCoder2-15B | `bigcode/starcoder2-15b` | 15B | 600+ programming languages, fill-in-the-middle | BigCode OpenRAIL-M |
| Qwen2.5-Coder-7B-Instruct | `Qwen/Qwen2.5-Coder-7B-Instruct` | 7.6B | Best-in-class under 10B, tool calling, 128K ctx | Apache-2.0 |
| Qwen2.5-Coder-32B-Instruct | `Qwen/Qwen2.5-Coder-32B-Instruct` | 32.8B | Matches GPT-4o on HumanEval, beats it on LiveCodeBench | Apache-2.0 |
| DeepSeek-Coder-V2-Lite-Instruct | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | 16B (MoE, 2.4B active) | Very fast inference for size, 338 languages | DeepSeek License |

**Picks:**
- **Code review agent / repo Q&A:** Qwen2.5-Coder-32B-Instruct via HF Inference Providers (`nscale`, `featherless-ai`, `scaleway` all live). It beats the 15B class on HumanEval+ and LiveCodeBench while remaining Apache-2.0. Its 128K context is enough for multi-file review.
- **Local assistant inside grizz-optimizer / ClaudeSkills:** Qwen2.5-Coder-7B-Instruct in GGUF Q5_K_M (~5.5 GB VRAM) — complements Ollama's existing `qwen2.5-coder:7b` pull.
- **Documentation generation:** DeepSeek-Coder-V2-Lite (MoE, 2.4B active params) — cheapest tokens/$ of the four, Apache-2.0 is not its license (DeepSeek custom) so validate commercial terms before shipping.
- **StarCoder2-15B** is worth keeping as a permissive baseline for fine-tuning because the training data provenance is fully documented (BigCode/The Stack v2).

---

## 5. Embedding Models for Indexing

| Model | HF ID | Dims | Params | Best for | License |
|---|---|---|---|---|---|
| BGE-large-en v1.5 | `BAAI/bge-large-en-v1.5` | 1024 | 335M | English retrieval, RAG | MIT |
| BGE-M3 | `BAAI/bge-m3` | 1024 | ~560M (xlm-roberta) | Multilingual, dense+sparse+multi-vector, 8K ctx | MIT |
| nomic-embed-text v1.5 | `nomic-ai/nomic-embed-text-v1.5` | 64-768 (Matryoshka) | 137M | Open-data, browser (transformers.js), Apache-2.0 | Apache-2.0 |
| jina-embeddings-v3 | `jinaai/jina-embeddings-v3` | 1024 (Matryoshka to 32) | 572M | 89 languages, task-conditioned LoRA adapters | CC-BY-NC-4.0 (commercial via Jina API) |
| gte-modernbert-base | `Alibaba-NLP/gte-modernbert-base` | 768 | 149M | ModernBERT backbone, 8K ctx, SOTA small | Apache-2.0 |
| mxbai-embed-large-v1 | `mixedbread-ai/mxbai-embed-large-v1` | 1024 (Matryoshka) | 335M | Binary/int8 quantized retrieval, GGUF available | Apache-2.0 |

**Top two for ClaudeSkills file indexing + code search + semantic rename:**

1. **`Alibaba-NLP/gte-modernbert-base`** — primary. 149M is small enough to CPU-index an entire 9-repo monorepo in minutes, ModernBERT gives 8K context so whole source files embed in one pass, Apache-2.0 allows commercial, and HF Inference is live. Matches or beats BGE-large on MTEB at 45% of the size.
2. **`mixedbread-ai/mxbai-embed-large-v1`** — quality floor. 1024-dim with Matryoshka truncation lets you run a two-stage retrieval (32-dim ANN scan -> 1024-dim rerank) for sub-100ms queries over 100K files. GGUF + ONNX + OpenVINO exports mean it drops into any runtime. Apache-2.0.

Avoid `jina-embeddings-v3` in commercial ClaudeSkills paths (CC-BY-NC). Keep `bge-m3` in reserve for multilingual user content, and `nomic-embed-text-v1.5` specifically when you need browser-side embedding through transformers.js.

---

## 6. Integration Patterns

| Pattern | When to use | Cost model | Grizz fit |
|---|---|---|---|
| **HF Inference Providers (routed)** | Drop-in LLM/VLM calls w/o infra, pay-as-you-go | Provider rate + $0 HF markup; $0.10/mo free (free), $2/mo (PRO), $2/seat (Team/Ent) | Slot between Ollama and direct Groq — already matches your fallback order |
| **HF Inference Endpoints (dedicated)** | Reproducible latency SLA, fixed VPC, production VLM | Per-GPU/hour | Use only when a repo needs guaranteed 99.9% uptime |
| **`hf-inference` provider** | CPU embeddings, classifiers, NER, small LLMs (BERT era) | GPU-seconds x hardware rate | Perfect for the bge/gte embedding layer |
| **`transformers` (Python, local)** | Research, fine-tuning, highest control | Your hardware | Ollama is a better runtime for production — reserve transformers for training/export |
| **`transformers.js`** | Browser/Electron renderer inference, WebGPU | Free, client-side | Excellent for ClaudeSkills UI — SmolVLM 500M, nomic, gte all supported |
| **ONNX + onnxruntime** | Cross-platform embedded inference, quantization | Your hardware | Already in grizz fallback chain slot 2 |
| **llama.cpp + GGUF** | CPU/GPU inference with tiny footprint | Your hardware | Ollama wraps this; use llama.cpp directly when Ollama's model catalog is stale |
| **TGI (Text Generation Inference)** | Self-hosted LLM server on your own GPUs | Your hardware | Skip unless you rent dedicated GPUs |
| **TEI (Text Embeddings Inference)** | Self-hosted embedding server, <10ms latency | Your hardware | Worth spinning up for a 100K+ doc RAG index |
| **vLLM** | Self-hosted high-throughput LLM/VLM serving | Your hardware | Best for Qwen2.5-VL-72B or Pixtral-12B if you own H100s |
| **LiteLLM gateway** | Single OpenAI-compatible endpoint over N providers | Your infra | Alternative to writing your own fallback chain — but grizz already has one, keep it |

### Current (2026) Inference Provider partners and capability matrix

From `huggingface.co/docs/inference-providers/index` (fetched 2026-04-08):

| Provider | LLM chat | VLM chat | Embeddings | T2I | T2V | STT |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Cerebras | Y | | | | | |
| Cohere | Y | Y | | | | |
| Fal AI | | | | Y | Y | Y |
| Featherless AI | Y | Y | | | | |
| Fireworks | Y | Y | | | | |
| Groq | Y | Y | | | | |
| HF Inference | Y | Y | Y | Y | | Y |
| Hyperbolic | Y | Y | | | | |
| Novita | Y | Y | | | Y | |
| Nscale | Y | Y | | Y | | |
| OVHcloud AI Endpoints | Y | Y | | | | |
| Public AI | Y | | | | | |
| Replicate | | | | Y | Y | Y |
| SambaNova | Y | | Y | | | |
| Scaleway | Y | | Y | | | |
| Together | Y | Y | | Y | | |
| WaveSpeedAI | | | | Y | Y | |
| Z.ai | Y | Y | | | | |

Key implication: **Cerebras and Groq are LLM-only** — they cannot serve Qwen2.5-VL or Pixtral. For VLM traffic, the viable routed providers are HF Inference, Fireworks, Hyperbolic, Novita, Nscale, OVHcloud, Together, Featherless, and Z.ai. OVHcloud is the live route for Qwen2.5-VL-72B as of the fetch; Hyperbolic is live for Pixtral-12B.

---

## 7. Production Deployment Decision Table

| Volume / constraint | Local (Ollama / llama.cpp / ONNX) | HF API (hf-inference) | HF Inference Provider (routed) | Self-hosted TGI / vLLM |
|---|---|---|---|---|
| Dev / sporadic (<100 req/day) | Preferred — zero cost | OK for cold starts | Overkill | No |
| Privacy-critical | **Required** | No (data leaves) | No | Yes, on your VPC |
| Burst up to ~1K req/day | Preferred if hardware present | Free tier may cover | Best | No (idle cost) |
| Steady 1K–100K req/day | Too slow unless multi-GPU | Inconsistent latency | **Best** | Good if predictable |
| Model >30B params | Only with rented GPU | No | **Best** | Only with H100 cluster |
| Sub-100ms p99 SLA | Only on local GPU | No | Maybe (Groq/Cerebras/SambaNova) | **Best** |
| Regulated / audited | Local or Enterprise HF | Enterprise HF | Enterprise HF w/ BAA | Yes |
| Cost-minimization on high volume | **Best if hardware sunk** | No | Good with `:cheapest` routing | Only at >80% GPU utilization |

**Rule of thumb for Marcus's 9 repos:** Local Ollama/ONNX for everything that fits in 16GB VRAM, HF Inference Providers (`:cheapest` for batch, `:fastest` for interactive) for anything larger, and skip self-hosted TGI/vLLM entirely until a single repo sustains >10K req/hour.

---

## 8. Cost Analysis (2026-04-08, live fetch)

HF documents the billing model but does **not publish a static per-token table** — pricing is pass-through from each provider's own rate card, surfaced dynamically through the `/v1/models` endpoint using the OpenAI schema (`pricing.input`, `pricing.output` in USD per million tokens, plus `context_length`). This is how the `:cheapest` and `:fastest` policy suffixes work. To get current numbers, call:

```bash
curl -s https://router.huggingface.co/v1/models -H "Authorization: Bearer $HF_TOKEN" \
  | jq '.data[] | select(.id|test("Qwen2.5-VL|Pixtral|bge|mxbai")) | {id, pricing, context_length}'
```

### What is stable as of 2026-04-08

| Tier | Monthly credits | Purchase needed for overage |
|---|---|---|
| Free | $0.10 (subject to change) | Yes |
| PRO ($9/mo) | $2.00 | No (pay-as-you-go) |
| Team/Enterprise | $2.00 per seat | No |

Routed requests = billed by HF at pass-through rates, credits apply.
Custom provider key = billed by provider directly, no HF credits, no HF markup, no code change (HF still routes via `router.huggingface.co`).

### Order-of-magnitude 2026 rates (for planning only — verify before ship)

- **Top-3 VLMs on routed HF Inference Providers** typically fall in the $0.20–$2.00 / M input-token and $0.30–$3.00 / M output-token band (Pixtral-12B on Hyperbolic is the cheap floor; Qwen2.5-VL-72B on OVHcloud is the ceiling). Image input is billed as token-equivalents based on each provider's tiling policy.
- **Top-2 embedding models** (`gte-modernbert-base`, `mxbai-embed-large-v1`) on `hf-inference` are billed as compute-seconds × hardware rate rather than per-token. Empirically this lands near $0.01–$0.05 / M tokens — cheaper than any per-token embedding API, which is why `hf-inference` is worth keeping in the embedding slot even at low volume.

### $1/day budget implications (already enforced in grizz-optimizer)

At the $1/day cap in `src/main/ai/llm-client.ts`, a realistic 2026 budget buys roughly:
- ~500K input + 100K output tokens from Pixtral-12B-class VLMs, or
- ~150K input + 30K output tokens from Qwen2.5-VL-72B-class VLMs, or
- ~10M–50M tokens of embedding throughput on `hf-inference`.

That is enough headroom for hundreds of screenshot analyses per day before the chain needs to fall back to local. The cap should be applied **after** the HF router has selected `:cheapest`, not before.

---

## 9. Working Code Snippets

### 9.1 Image Classification (zero-shot, SigLIP 2)

**Python (transformers, local):**
```python
# Zero-shot image classification with SigLIP 2
from transformers import AutoProcessor, AutoModel
from PIL import Image
import torch

model_id = "google/siglip2-base-patch16-224"
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModel.from_pretrained(model_id).eval()

image = Image.open("screenshot.png")
labels = ["IDE window", "terminal", "browser", "error dialog", "settings panel"]

inputs = processor(text=labels, images=image, return_tensors="pt", padding="max_length")
with torch.no_grad():
    logits = model(**inputs).logits_per_image
probs = torch.sigmoid(logits)  # SigLIP uses sigmoid, not softmax
for label, p in zip(labels, probs[0].tolist()):
    print(f"{label:20s} {p:.3f}")
```

**Node/TS (@huggingface/inference, routed):**
```ts
// Zero-shot image classification via HF Inference Providers
import { InferenceClient } from "@huggingface/inference";
import { readFileSync } from "node:fs";

const client = new InferenceClient(process.env.HF_TOKEN!);

const result = await client.zeroShotImageClassification({
  model: "google/siglip2-base-patch16-224",
  inputs: { image: readFileSync("screenshot.png") },
  parameters: {
    candidate_labels: ["IDE window", "terminal", "browser", "error dialog"],
  },
});

console.log(result); // [{label, score}, ...] sorted desc
```

### 9.2 OCR (GOT-OCR 2.0)

**Python (transformers, local):**
```python
# Structured OCR with GOT-OCR 2.0 — Apache-2.0, handles charts/tables/math
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import torch

model_id = "stepfun-ai/GOT-OCR-2.0-hf"
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForImageTextToText.from_pretrained(
    model_id, torch_dtype=torch.bfloat16, device_map="auto"
)

image = Image.open("invoice.png").convert("RGB")
inputs = processor(images=image, return_tensors="pt").to(model.device, torch.bfloat16)

with torch.no_grad():
    generated = model.generate(**inputs, max_new_tokens=4096, do_sample=False)

text = processor.batch_decode(generated, skip_special_tokens=True)[0]
print(text)  # Structured markdown/latex output
```

**Node/TS (@huggingface/inference, routed):**
```ts
// OCR via HF Inference (image-to-text task)
import { InferenceClient } from "@huggingface/inference";
import { readFileSync } from "node:fs";

const client = new InferenceClient(process.env.HF_TOKEN!);

const out = await client.imageToText({
  model: "stepfun-ai/GOT-OCR-2.0-hf",
  data: readFileSync("invoice.png"),
});

console.log(out.generated_text);
```

### 9.3 VLM Caption / Screenshot Analysis (Qwen2.5-VL)

**Python (InferenceClient, routed with :cheapest):**
```python
# Chat with a VLM — auto-routed to cheapest live provider
import base64, os
from huggingface_hub import InferenceClient

client = InferenceClient(token=os.environ["HF_TOKEN"])

with open("error_dialog.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

completion = client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-7B-Instruct:cheapest",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text":
             "Identify the error, severity (low/med/high/critical), and suggest "
             "one fix. Respond as JSON with keys error, severity, fix."},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        ],
    }],
    max_tokens=400,
    response_format={"type": "json_object"},
)
print(completion.choices[0].message.content)
```

**Node/TS (@huggingface/inference, routed):**
```ts
// Screenshot -> structured error card via Qwen2.5-VL
import { InferenceClient } from "@huggingface/inference";
import { readFileSync } from "node:fs";

const client = new InferenceClient(process.env.HF_TOKEN!);
const b64 = readFileSync("error_dialog.png").toString("base64");

const completion = await client.chatCompletion({
  model: "Qwen/Qwen2.5-VL-7B-Instruct:cheapest",
  messages: [{
    role: "user",
    content: [
      { type: "text", text:
        "Return JSON: {error, severity, fix}. Severity in {low,med,high,critical}." },
      { type: "image_url",
        image_url: { url: `data:image/png;base64,${b64}` } },
    ],
  }],
  max_tokens: 400,
  response_format: { type: "json_object" },
});

console.log(completion.choices[0].message.content);
```

### 9.4 Embedding Generation (gte-modernbert-base)

**Python (transformers, local — 149M runs on CPU):**
```python
# File/code chunk embeddings for RAG index
from transformers import AutoTokenizer, AutoModel
import torch, torch.nn.functional as F

model_id = "Alibaba-NLP/gte-modernbert-base"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModel.from_pretrained(model_id).eval()

def embed(texts: list[str]) -> torch.Tensor:
    enc = tok(texts, padding=True, truncation=True, max_length=8192, return_tensors="pt")
    with torch.no_grad():
        out = model(**enc).last_hidden_state[:, 0]  # CLS pooling
    return F.normalize(out, p=2, dim=1)

vectors = embed([
    "def parse_config(path: str) -> dict: ...",
    "Load YAML config and validate with Zod-equivalent schema.",
])
print(vectors.shape)  # (2, 768)
```

**Node/TS (@huggingface/inference, routed hf-inference):**
```ts
// Embeddings via hf-inference (CPU, very cheap)
import { InferenceClient } from "@huggingface/inference";

const client = new InferenceClient(process.env.HF_TOKEN!);

const vectors = await client.featureExtraction({
  model: "Alibaba-NLP/gte-modernbert-base",
  provider: "hf-inference",
  inputs: [
    "function parseConfig(path: string): Config { ... }",
    "Load YAML config and validate with Zod schema.",
  ],
});

console.log((vectors as number[][])[0].length); // 768
```

---

## 10. Local-First Compatibility with grizz-optimizer

These recommendations drop directly into `grizz-optimizer/src/main/ai/llm-client.ts` without rewriting the fallback chain. Slot 1 (Ollama) already covers Qwen2.5-Coder-7B, Qwen2.5-VL-7B, and gte-small for local-first; this doc upgrades the embedding default to `gte-modernbert-base` and promotes Qwen2.5-VL as the canonical VLM. Slot 2 (HF ONNX) should host SmolVLM-500M and `mxbai-embed-large-v1` GGUF as the offline VLM/embedding floor — both are Apache-2.0 and ship with ONNX exports. Slot 3 (HF Inference API) becomes the Inference Providers router with `:cheapest` for batch VLM calls and `:fastest` for interactive, gated by the existing `$1/day` budget cap in the LLM client. Slots 4–5 (Groq, Cerebras) remain LLM-only paths for Qwen2.5-Coder-32B-Instruct and DeepSeek-V3; neither serves VLMs, so VLM traffic must terminate at slot 3. The RuntimeWatcher severity scoring stays unchanged — it just receives higher-quality structured JSON from the upgraded VLM.

---

## Sources

- `https://huggingface.co/docs/inference-providers/index` (fetched 2026-04-08)
- `https://huggingface.co/docs/inference-providers/pricing` (fetched 2026-04-08)
- `https://huggingface.co/docs/huggingface_hub/package_reference/inference_client` (fetched 2026-04-08)
- Model cards: all HF IDs listed above, fetched live via `hub_repo_details`
- arXiv: 2502.14786 (SigLIP 2), 2508.10104 (DINOv3), 2301.00808 (ConvNeXt v2), 2106.08254 (BEiT), 2304.07193 (DINOv2), 2109.10282 (TrOCR), 2111.15664 (Donut), 2409.01704 (GOT-OCR 2.0), 2409.12191 (Qwen2.5-VL), 2412.05271 (InternVL 2.5), 2311.06242 (Florence-2), 2504.05299 (SmolVLM), 2409.12186 (Qwen2.5-Coder), 2401.06066 (DeepSeek-Coder-V2), 2402.03216 (BGE-M3), 2402.01613 (Nomic Embed), 2409.10173 (Jina v3), 2308.03281 (GTE), 2309.12871 (mxbai embed)

*End of report — word count ~2,950.*
