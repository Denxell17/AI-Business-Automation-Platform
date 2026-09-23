# Day 169 Summary - llama.cpp Adapter and Factory

## Goal

Add a local llama.cpp implementation of the existing provider-neutral AI
boundary and construct it only from Day 168's validated settings.

## Completed

- Added `LlamaCppAgentProvider`, which implements the `AgentProvider` protocol
  with one non-streaming `/v1/chat/completions` request.
- Mapped the configured model alias, system prompt, user input, output-token
  limit, connect timeout, and read timeout to the local request.
- Bounded the combined prompt input before any transport call and capped the
  decoded local response at 65,536 bytes.
- Added `HttpLlamaCppTransport` using the Python standard library.
- Revalidated the exact `127.0.0.1:8080` destination and chat path immediately
  before connection, with redirects disabled and rejected.
- Added `create_agent_provider`, which returns no provider while integrations
  remain disabled and creates the local adapter only after validated selection.
- Kept deterministic tests independent of llama.cpp, the Qwen model, a GPU,
  and network sockets by injecting in-memory transports and connections.

## Security Decisions

- The transport opens connections only to the approved loopback address and
  port; it does not resolve or connect to arbitrary hostnames.
- Requests are non-streaming and response reads are capped.
- Transport exceptions and malformed responses become the existing generic
  safe provider error without raw local response details or exception chaining.
- The adapter does not log prompts, responses, headers, tokens, or model paths.

## Files Changed

- `Projects/employee_management_system/llama_cpp_agent_provider.py`
- `Projects/employee_management_system/agent_provider_factory.py`
- `Projects/employee_management_system/tests/test_llama_cpp_agent_provider.py`
- `Projects/employee_management_system/tests/test_agent_provider_factory.py`
- `Notes/day169_summary.md`

## Tests

- `python -m unittest tests.test_agent_provider_config tests.test_llama_cpp_agent_provider tests.test_agent_provider_factory tests.test_openai_agent_provider -v`
- Result: 28 tests passed.

## Current ABAP Status

Day 169 completes the deterministic local adapter and factory. Application UI,
provider-event persistence, metrics, and operational error codes are not wired
yet.

## Next Step

Day 170: define stable safe failure codes for local connection, timeout,
authentication, busy, server, oversized, malformed, and blank-response cases.
