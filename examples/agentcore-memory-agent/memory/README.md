# memory/

Abstraction layer over AgentCore's memory data-plane APIs.

## Files

### `manager.py`

The `MemoryManager` class provides four operations:

| Method | Purpose |
|--------|---------|
| `store_turn(actor_id, session_id, user_message, assistant_message)` | Records a conversation turn as an event. AgentCore asynchronously extracts long-term memories from accumulated events. |
| `retrieve(actor_id, query, max_results)` | Semantic search across all memory strategies for a given user. Returns the top-N most relevant memory records. |
| `close_session(actor_id, session_id)` | Signals session end so AgentCore generates a summary memory record. |
| `delete_actor_memories(actor_id)` | GDPR compliance: deletes all stored memories for a user. Called by the `/forget` Telegram command. |

## Memory Strategies

The memory store is created with three strategies (configured in `scripts/setup_memory.py`):

**Session Summary** (`/summaries/{actorId}/{sessionId}/`)
Generated when a session ends. Provides a compressed view of what happened in each conversation.

**User Preference** (`/preferences/{actorId}/`)
Extracted from conversation patterns. Captures things like communication style preferences, interests, and settings.

**Semantic Facts** (`/facts/{actorId}/`)
Extracted factual knowledge. Stores concrete information mentioned in conversations (names, dates, project details, etc.).

## Write Path

```
User message + Agent response
        │
        ▼
  store_turn() → CreateEvent API
        │
        ▼
  AgentCore background processing
        │
        ├── Summary strategy → session summary record
        ├── Preference strategy → preference record
        └── Semantic strategy → fact record
```

Events are the raw input. Long-term memory records are the processed output. There's an asynchronous delay between writing events and memories becoming retrievable.

## Read Path

```
User message (new turn)
        │
        ▼
  retrieve() → RetrieveMemoryRecords API
        │
        ▼
  Top-N records (ranked by relevance)
        │
        ▼
  Injected into system prompt
```

The semantic search works across all three strategy types simultaneously, returning a mixed set of summaries, preferences, and facts ranked by relevance to the query.

## Error Handling

All methods use best-effort semantics:
- `retrieve()` returns `[]` on failure (the agent still works, just without memory context)
- `store_turn()` logs errors but doesn't crash the agent
- `delete_actor_memories()` logs errors (the `/forget` command reports success regardless to avoid confusing the user, but logs the failure for ops)
