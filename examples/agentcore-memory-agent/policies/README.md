# policies/

Cedar security policies enforced at the AgentCore Gateway boundary.

## Files

### `agent_policies.cedar`

Defines what the agent is and isn't allowed to do. These policies are evaluated outside the agent's code — the LLM cannot bypass or modify them.

## Policy Summary

| Section | What It Controls |
|---------|-----------------|
| **Code Interpreter** | Agent can run bash and python in the sandbox. No other languages allowed. |
| **Browser Search** | Agent can use the search tool freely. |
| **Browser URL Fetch** | Agent can fetch URLs, but navigation to private IP ranges (10.x, 172.16.x, 192.168.x, localhost, 127.x) is blocked. |
| **Telegram Send** | Agent can send messages, documents, and photos only to the user who initiated the request (`chat_id == actorId`). |
| **Memory** | Agent can read and write to the TelegramAgentMemory store. |
| **Default Deny** | Everything not explicitly permitted is forbidden. New tools added without a policy will be silently blocked. |

## How Cedar Works

Cedar uses a deny-by-default model. Access is only granted through explicit `permit` statements. The `forbid` statement at the bottom is technically redundant (Cedar denies by default), but it's included for clarity and to catch unintended tool additions.

Each policy has three components:
- **Principal:** Who is making the request (our agent)
- **Action:** What they're trying to do (invoke a tool, read memory, etc.)
- **Resource:** What they're acting on (a specific tool, memory store)
- **Conditions:** `when` (additional requirements) and `unless` (exceptions)

## Key Security Decisions

**User-scoped Telegram messaging:** The `when { resource.toolInput.chat_id == context.session.actorId }` condition ensures the agent can only message the user who triggered the request. This prevents the agent from being manipulated into spamming other users.

**Private IP blocking:** The browser URL fetch blocks navigation to internal networks (`10.x`, `172.16.x`, `192.168.x`, `localhost`). This prevents SSRF attacks where the agent might be tricked into accessing internal services.

**Language restriction:** Code Interpreter is limited to `bash` and `python`, preventing potential exploits through less-common language runtimes.

## Modifying Policies

Edit `agent_policies.cedar` and redeploy. Cedar policies support natural language authoring through the AgentCore console as well — describe the rule in English and it generates validated Cedar.

When adding a new tool:
1. Add a `permit` statement for the tool
2. Include appropriate `when`/`unless` conditions
3. Test by invoking the agent and checking CloudWatch for policy evaluation logs

## References

- [Cedar Policy Language](https://www.cedarpolicy.com/)
- [AgentCore Policy Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)
