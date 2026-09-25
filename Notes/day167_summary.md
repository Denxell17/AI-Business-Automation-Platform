# Day 167 Summary - Local Qwen Runtime Baseline

## Goal

Install and verify the local Qwen runtime required before ABAP implements its
provider-independent llama.cpp adapter.

## Completed

- Installed llama.cpp version `0.4.1-dev`, build `11095`, commit `58367713a`.
- Verified the installed Windows Vulkan build can use the NVIDIA RTX 2050.
- Downloaded the official Qwen2.5 3B Instruct Q4_K_M GGUF outside Git.
- Recorded the model SHA-256:

  `626B4A6678B86442240E33DF819E00132D3BA7DDDFE1CDC4FBB18E0A9615C62D`

- Kept the model and local API key file in `~/Models/ABAP`, outside the
  repository.
- Restricted the local key file to the current Windows user.
- Started llama.cpp on the exact loopback address `127.0.0.1:8080`.
- Disabled the llama.cpp Web UI.
- Configured one request slot and authenticated local API access.
- Verified an unauthenticated generation request returns HTTP `401`.
- Verified one authenticated synthetic business request succeeds.
- Confirmed the model response was generated locally.

## Resource Evidence

- GPU: NVIDIA RTX 2050 with 4 GB VRAM.
- Idle loaded VRAM: 2,019 MiB of 4,096 MiB.
- llama.cpp process working set: approximately 2,026 MiB.
- Available system RAM before loading: 3.98 GiB.
- Available system RAM while loaded: 1.79 GiB.
- Synthetic request prompt processing: 25.54 tokens per second.
- Synthetic request generation: 49.95 tokens per second.
- Synthetic request total time: 2.56 seconds for 88 tokens.

## Important Technical Decisions

- Qwen2.5 3B Instruct Q4_K_M remains the selected local model.
- The tested runtime is the pinned llama.cpp Windows Vulkan build 11095.
- ABAP will use the existing provider-independent `AgentProvider` boundary.
- The local server binds only to loopback and requires a local API token.
- The server must run on demand and stop after use.
- Start the server only when at least 4 GiB of system RAM is available before
  loading the model.
- Future ABAP use will begin with a 2,048-token context, one request slot, and
  bounded output to reduce laptop resource pressure.
- No model, API key, prompt, or response is committed to Git or stored in
  normal application logs.

## Files Changed

- `Notes/milestone6_local_qwen_implementation_plan.md`
- `Notes/day167_summary.md`

## Tests

- llama.cpp version check passed.
- Model file SHA-256 was calculated.
- Local server loaded successfully.
- Loopback listener started successfully.
- Unauthenticated generation returned HTTP `401`.
- Authenticated synthetic generation completed successfully.
- GPU and system RAM measurements were captured.
- No ABAP application code changed, so the automated ABAP test suite was not
  required for this day.

## Current ABAP Status

Day 167 completes the local runtime baseline for Milestone 6. The Qwen model
and llama.cpp server are verified locally, but ABAP does not yet construct or
call the local provider.

## Next Step

Day 168: implement fail-closed local-provider configuration so ABAP constructs
no AI client unless the integration gate, provider selection, loopback endpoint,
token, model alias, and bounded limits all validate.