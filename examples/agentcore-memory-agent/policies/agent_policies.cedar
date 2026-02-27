// ==========================================================================
// Cedar Policies for telegram-memory-agent
// ==========================================================================
// These policies are enforced at the AgentCore Gateway boundary, outside
// agent code, providing deterministic guardrails the LLM cannot bypass.
//
// Docs: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html
// Cedar: https://www.cedarpolicy.com/
// ==========================================================================


// --------------------------------------------------------------------------
// 1. CODE INTERPRETER (Bash) — Allow with restrictions
// --------------------------------------------------------------------------

// Allow the agent to execute bash commands in the sandbox
permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"InvokeTool",
    resource == AgentCore::Tool::"code-interpreter"
)
when {
    // Only allow bash and python — no arbitrary language injection
    resource.toolInput.language in ["bash", "python"]
};


// --------------------------------------------------------------------------
// 2. BROWSER — Allow web search and page fetching
// --------------------------------------------------------------------------

// Allow the agent to create browser sessions
permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"InvokeTool",
    resource == AgentCore::Tool::"browser-search"
);

permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"InvokeTool",
    resource == AgentCore::Tool::"browser-fetch-url"
)
unless {
    // Block navigation to internal/private networks
    resource.toolInput.url like "http://10.*"      ||
    resource.toolInput.url like "http://172.16.*"   ||
    resource.toolInput.url like "http://192.168.*"  ||
    resource.toolInput.url like "http://localhost*"  ||
    resource.toolInput.url like "http://127.*"
};


// --------------------------------------------------------------------------
// 3. TELEGRAM — Allow messaging, scoped to the requesting user
// --------------------------------------------------------------------------

// Allow sending text messages only to the user who initiated the request
permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"InvokeTool",
    resource == AgentCore::Tool::"telegram-send-message"
)
when {
    // The chat_id in the tool input must match the actor's Telegram ID
    resource.toolInput.chat_id == context.session.actorId
};

// Allow sending documents to the requesting user
permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"InvokeTool",
    resource == AgentCore::Tool::"telegram-send-document"
)
when {
    resource.toolInput.chat_id == context.session.actorId
};

// Allow sending photos to the requesting user
permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"InvokeTool",
    resource == AgentCore::Tool::"telegram-send-photo"
)
when {
    resource.toolInput.chat_id == context.session.actorId
};


// --------------------------------------------------------------------------
// 4. MEMORY — Allow read/write for the agent
// --------------------------------------------------------------------------

permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"ReadMemory",
    resource == AgentCore::Memory::"TelegramAgentMemory"
);

permit(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"WriteMemory",
    resource == AgentCore::Memory::"TelegramAgentMemory"
);


// --------------------------------------------------------------------------
// 5. DEFAULT DENY — Block everything not explicitly permitted
// --------------------------------------------------------------------------

// This is implicit in Cedar (deny by default), but we add an explicit
// forbid for documentation clarity and to catch any new tools added later.

forbid(
    principal == AgentCore::Agent::"telegram-memory-agent",
    action == AgentCore::Action::"InvokeTool",
    resource
)
unless {
    resource in [
        AgentCore::Tool::"code-interpreter",
        AgentCore::Tool::"browser-search",
        AgentCore::Tool::"browser-fetch-url",
        AgentCore::Tool::"telegram-send-message",
        AgentCore::Tool::"telegram-send-document",
        AgentCore::Tool::"telegram-send-photo"
    ]
};
