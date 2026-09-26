# Milestone 6 OpenAI Connection Contract

## Selected Provider

OpenAI is the selected external provider for Milestone 6.

ABAP will use the existing provider-independent AgentProvider interface and
OpenAIAgentProvider adapter.

## Portfolio Demonstration

An authorized administrator submits one synthetic business question through
the existing AI Assistant page.

ABAP sends the request through the provider-independent adapter and displays
either a validated text response or a fixed safe error.

## Allowed Outbound Data

- Selected model name
- ABAP-owned system instructions
- Synthetic user input
- Data intentionally entered for the approved AI operation

## Prohibited Outbound Data

- API keys
- Passwords
- Session tokens
- Database credentials or URLs
- Webhook signing secrets
- Private documents
- Unnecessary customer or employee personal information
- Raw application exceptions

## Configuration

- ABAP_INTEGRATIONS_ENABLED controls the global integration gate.
- ABAP_EXTERNAL_PROVIDER selects the external provider.
- OPENAI_API_KEY contains the provider credential.
- OPENAI_TIMEOUT_SECONDS controls the bounded request timeout.
- AI_ASSISTANT_MODEL selects the configured model.

Integrations must be disabled by default.

ABAP_EXTERNAL_PROVIDER=disabled means no external provider client may be
constructed.

## Endpoint Policy

ABAP uses only the official OpenAI API endpoint.

Milestone 6 will not permit an environment variable or user input to redirect
requests to a custom provider endpoint.

## Credential Policy

The OpenAI credential must:

- Belong to the ABAP development project.
- Have the smallest permissions supported by the provider.
- Be stored in an ignored local environment or deployment secret manager.
- Never appear in Git, screenshots, logs, browser responses, test fixtures, or
  stored provider events.

## Timeout Policy

The request timeout defaults to 30 seconds.

Accepted timeout values are between 1 and 120 seconds.

## Rate-Limit Policy

Interactive requests are not automatically retried.

A rate limit becomes the safe internal failure code `rate_limited`. The user may
retry later.

Background retry behavior must be explicitly bounded before it is introduced.

## Safe Failure Codes

- authentication_failed
- rate_limited
- timeout
- connection_failed
- provider_unavailable
- invalid_response
- configuration_invalid

Raw provider exception messages must not be shown to users or stored.

## Stored Operational Data

ABAP may store:

- Provider name
- Operation name
- Started, succeeded, or failed status
- Safe failure code
- Request duration
- Creation and completion timestamps

ABAP must not store prompts, responses, credentials, authorization headers, or
raw provider errors in integration event records.

## Cost Control

Automated tests use deterministic substitute clients and make no network calls.

Only one small controlled live request is required for the final Milestone 6
demonstration.

## Credential Rotation

1. Create a new restricted provider key.
2. Update the local secret store or deployment secret manager.
3. Restart or redeploy ABAP.
4. Perform one synthetic smoke request.
5. Confirm that a successful provider event was stored.
6. Revoke the old key.
7. Verify that no new authentication failures appear.
8. Record the rotation date without recording either credential.

## Exit Evidence

Milestone 6 requires:

- Deterministic configuration and adapter tests
- Safe timeout and rate-limit behavior
- Provider event storage
- Integration health metrics
- SQLite and PostgreSQL verification
- One controlled live demonstration
- A documented credential-rotation procedure