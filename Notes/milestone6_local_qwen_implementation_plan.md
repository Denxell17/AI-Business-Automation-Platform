# Milestone 6 Local Qwen Implementation Plan

## Decision

Milestone 6 will use Qwen2.5 3B Instruct through a local llama.cpp HTTP
server. OpenAI is not the selected Milestone 6 provider.

ABAP will preserve its existing `AgentProvider` protocol. Business services
will depend on that protocol rather than llama.cpp, Qwen, GGUF, or an
OpenAI-compatible response format. A later provider change must require a new
adapter and configuration selection, not a redesign of the AI Assistant.

## Selected Local Runtime

- Model repository: `Qwen/Qwen2.5-3B-Instruct-GGUF`
- Model file: `qwen2.5-3b-instruct-q4_k_m.gguf`
- Quantization: Q4_K_M
- Approximate model-file size: 2.1 GB
- Runtime: the pinned llama.cpp Windows Vulkan build 11095
- Transport: HTTP on the exact loopback address `127.0.0.1`
- API shape: llama.cpp's OpenAI-compatible chat endpoint
- Concurrent request slots: one

The GGUF file, llama.cpp binaries, caches, and generated output do not belong
in Git. Store them outside the repository and record only version, filename,
source, license, and integrity-hash information.

## Laptop-Safe Starting Profile

Target hardware:

- AMD Ryzen 5 8645HS: 6 cores / 12 threads
- 16 GB DDR5 RAM
- NVIDIA RTX 2050: 4 GB VRAM
- 512 GB NVMe SSD

Start with these conservative server controls:

| Control | Starting value | Reason |
| --- | --- | --- |
| Context size | 2048 tokens | Bounds KV-cache RAM and VRAM use. |
| Maximum generated tokens | 256 | Bounds latency and resource use. |
| Parallel slots | 1 | Prevents concurrent generations from multiplying memory use. |
| CPU generation threads | 6 | Uses the physical cores without occupying all 12 logical threads. |
| Batch size | 256 | Keeps prompt processing moderate on a laptop. |
| Micro-batch size | 128 | Reduces peak compute-buffer use. |
| GPU layers | `auto` | Lets current llama.cpp fit layers without assuming all layers fit. |
| GPU fit margin | 1024 MiB | Leaves VRAM for Windows and display use. |
| Process priority | low | Reduces interference with normal laptop use. |
| Polling | disabled | Avoids unnecessary idle CPU use. |
| HTTP host | `127.0.0.1` | Prevents LAN exposure. |
| Web UI | disabled | Exposes only the API needed by ABAP. |

Run the local model server on demand and only when at least 4 GiB of system RAM
is available before startup. Stop the server after the AI task finishes. The
verified Q4_K_M baseline used about 2.0 GiB of system RAM and 2.0 GiB of VRAM,
so unrelated memory-heavy applications should be closed first.

Do not begin with the model's maximum supported context, multiple parallel
slots, unlimited output, or forced full GPU offload. Measure first. If the
server reports GPU allocation failure, reduce GPU layers or run CPU-only. If
it remains responsive with safe VRAM headroom, increase GPU offload gradually.

The planned server profile is equivalent to:

```text
llama-server
  --model <outside-repository-path-to-q4_k_m.gguf>
  --alias qwen2.5-3b-instruct-q4_k_m
  --host 127.0.0.1
  --port 8080
  --ctx-size 2048
  --n-predict 256
  --parallel 1
  --threads 6
  --threads-batch 6
  --batch-size 256
  --ubatch-size 128
  --n-gpu-layers auto
  --fit on
  --fit-target 1024
  --prio -1
  --poll 0
  --no-webui
```

Confirm the exact options with the installed pinned `llama-server --help`.
llama.cpp changes over time, so the repository runbook must record the tested
version and command.

## Security and Privacy Contract

- `ABAP_INTEGRATIONS_ENABLED=false` remains the default.
- `ABAP_EXTERNAL_PROVIDER=disabled` means no local AI client is constructed.
- The selected provider value will be `llama_cpp`.
- ABAP accepts only the exact loopback llama.cpp origin; arbitrary URLs,
  hostnames, redirects, Unix sockets, and LAN addresses are rejected.
- llama.cpp binds only to `127.0.0.1`; it is not published to the LAN or
  internet.
- The llama.cpp Web UI, tools, agents, file access, and MCP features remain
  disabled.
- A generated local API token protects the server and is supplied through the
  environment or a local secret store, never a command-line argument or Git.
- ABAP sends only the configured model alias, fixed system instructions, and
  the authorized user's bounded input.
- Prompts, model responses, authorization headers, local API tokens, raw
  exceptions, and model paths are not written to provider event records or
  normal logs.
- Provider event records contain metadata only: provider, operation, status,
  safe failure code, duration, and timestamps.

## Configuration Contract

Planned settings:

| Variable | Default / rule |
| --- | --- |
| `ABAP_INTEGRATIONS_ENABLED` | `false`; strict boolean. |
| `ABAP_EXTERNAL_PROVIDER` | `disabled`; allowed enabled value is `llama_cpp`. |
| `ABAP_LOCAL_AI_MODEL` | Required when enabled; expected initial alias is `qwen2.5-3b-instruct-q4_k_m`. |
| `ABAP_LLAMA_CPP_BASE_URL` | Exact loopback value `http://127.0.0.1:8080/v1`; reject other destinations. |
| `ABAP_LLAMA_CPP_API_KEY` | Required when enabled; secret and never logged. |
| `ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS` | Bounded; initial value 2. |
| `ABAP_LOCAL_AI_READ_TIMEOUT_SECONDS` | Bounded; initial value 90. |
| `ABAP_LOCAL_AI_MAX_INPUT_CHARS` | Bounded; initial value 12000. |
| `ABAP_LOCAL_AI_MAX_OUTPUT_TOKENS` | Bounded; initial value 256. |

The model alias is configurable so ABAP can change models without changing
business-service code. The server remains responsible for mapping that alias
to the locally loaded GGUF.

## Safe Failure Codes

The adapter translates failures to fixed internal codes:

- `configuration_invalid`
- `local_ai_unavailable`
- `local_ai_loading`
- `timeout`
- `authentication_failed`
- `rate_limited`
- `invalid_response`


browser. Interactive requests are not automatically retried. The user may
retry later after a safe timeout, loading, busy, or unavailable response.

## Day-by-Day Implementation

### Day 167 — Contract and Hardware Baseline

1. Record this provider decision and the permitted data boundary.
2. Install or unpack a pinned Vulkan llama.cpp Windows release outside
   the repository.
3. Download the official Q4_K_M GGUF outside the repository.
4. Record llama.cpp version, Qwen model revision, filename, license, and file
   SHA-256 in the runbook. Do not record local usernames or private paths.
5. Start with the laptop-safe profile and verify `GET /health` on loopback.
6. Run one synthetic terminal prompt and record only timing and peak resource
   observations. Do not connect ABAP yet.
7. Verify the server is unreachable through the laptop's LAN address.

Exit: the local server answers on loopback, normal laptop use remains
responsive, and no model or binary is tracked by Git.

### Day 168 — Fail-Closed Local Provider Configuration

1. Replace the OpenAI-only configuration assumption with a provider selector.
2. Implement the disabled/`llama_cpp` state matrix.
3. Validate the exact loopback origin, model alias, local token, timeouts, and
   input/output limits without making a network request.
4. Keep existing OpenAI code isolated and unadvertised; do not delete working
   historical tests merely because it is not selected.
5. Add deterministic configuration tests for disabled, enabled, unknown,
   missing, malformed, padded, and unsafe values.

Exit: disabled mode cannot construct or contact a provider, and configuration
errors contain no token or private path.

### Day 169 — llama.cpp Adapter and Factory

1. Add `LlamaCppAgentProvider` implementing the existing `AgentProvider`
   protocol.
2. Add a provider factory that selects the adapter only from validated
   settings.
3. Map the protocol's model, system prompt, and input text to one bounded local
   chat request.
4. Disable streaming initially and read a bounded JSON response.
5. Reject redirects and revalidate that the destination is loopback when
   connecting.
6. Inject an in-memory transport in tests; unit tests never require llama.cpp,
   a model download, a GPU runtime, or a network socket.

Exit: deterministic adapter tests prove request mapping, response parsing,
model configurability, and provider independence.

### Day 170 — Safe Errors, Timeouts, and Busy Handling

1. Extend `AgentProviderError` with stable safe failure codes.
2. Map connection refusal, loading health, timeout, authentication failure,
   busy/rate-limited responses, server failure, oversized body, malformed JSON,
   and blank output.
3. Suppress exception chaining where raw local response details could leak.
4. Keep automatic retries disabled for interactive requests.
5. Confirm logs contain only safe codes, correlation IDs, and timing metadata.

Exit: every expected local runtime failure has a deterministic test and safe
browser behavior.

### Day 171 — Provider Event Storage

1. Add SQLite and PostgreSQL migration 008 for provider event metadata.
2. Store `started`, `succeeded`, or `failed`, plus provider, operation, safe
   failure code, duration, and timestamps.
3. Never store prompts, generated text, tokens, headers, response bodies, or
   model paths.
4. Add repository queries for recent attempts, successes, failures, timeouts,
   busy/rate-limit results, and last success.
5. Test SQLite and PostgreSQL behavior.

Exit: real provider operations create safe, queryable evidence.

### Day 172 — Metered Provider Wrapper

1. Add a provider-independent wrapper around any `AgentProvider`.
2. Insert the started event before contacting the runtime.
3. Measure duration with a monotonic clock.
4. Complete the event with success or a safe failure code.
5. Preserve the underlying safe error for the browser.
6. Inject the repository and clock in tests.

Exit: metrics do not require llama.cpp-specific code in business services.

### Day 173 — Application Wiring and Integration Health

1. Route AI Assistant and Agent Template execution through the validated
   provider factory and metered wrapper.
2. Preserve authentication, authorization, CSRF, length checks, and output
   escaping before provider construction or use.
3. Add an administrator-only integration-health view using stored events.
4. Report selected provider, configured/unavailable status, last attempt, last
   success, recent success count, and safe failure counts.
5. Do not contact llama.cpp from the public `/health` or `/ready` probes.
6. Do not reveal the token, model path, prompt, output, or raw error.

Exit: authorized users can use the local model and administrators can inspect
safe stored health evidence.

### Day 174 — Repeatable Local Demo and Exit Gate

1. Run focused deterministic tests and the complete local test suite.
2. Apply migration 008 and run live PostgreSQL tests.
3. Start the pinned llama.cpp server with the conservative profile.
4. Run one synthetic AI Assistant request and one safe failure demonstration.
5. Verify exactly one success and the expected failure metadata are stored.
6. Monitor Task Manager or `nvidia-smi` during the demo; record peak RAM, VRAM,
   response time, and whether normal laptop use remained responsive.
7. Document startup, shutdown, health check, model replacement, troubleshooting,
   local-token rotation, and CPU-only fallback.
8. Update the roadmap only after all exit evidence passes.

Exit: the demo is repeatable without cloud AI, raw data leakage, excessive
resource use, or business-service coupling to Qwen or llama.cpp.

## Local Token Rotation

1. Generate a new random local server token.
2. Stop llama.cpp.
3. Update the llama.cpp secret environment and ABAP secret environment without
   placing the token in shell history or Git.
4. Restart llama.cpp and ABAP.
5. Verify health and one synthetic request.
6. Remove the old token from the secret store.
7. Confirm no new authentication failures occur.
8. Record the date and result without recording either token.

## Milestone 6 Exit Checklist

- [ ] Qwen2.5 3B Instruct Q4_K_M and llama.cpp versions are pinned and recorded.
- [ ] Model and runtime files remain outside Git.
- [ ] llama.cpp binds only to loopback with Web UI and tool features disabled.
- [ ] The laptop-safe profile remains responsive under one request.
- [ ] Integrations are disabled by default.
- [ ] The model alias is configurable.
- [ ] Business services depend only on `AgentProvider`.
- [ ] Configuration, adapter, error, event, metric, and browser tests pass.
- [ ] No sensitive request or response content appears in events or logs.
- [ ] SQLite and PostgreSQL verification pass.
- [ ] A repeatable synthetic local demo passes.
- [ ] Startup, failure, model replacement, CPU fallback, and token rotation are
  documented.

## References

- Official Qwen GGUF model:
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
- Official llama.cpp server documentation:
  https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
