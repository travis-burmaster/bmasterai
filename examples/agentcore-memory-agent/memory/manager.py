"""
Memory Manager
==============
Wraps the AgentCore Memory data-plane APIs for:
  - Storing conversation turns as events (short-term memory)
  - Retrieving relevant long-term memories (summaries, preferences, facts)
  - Session lifecycle management

BMasterAI telemetry is emitted on every read/write operation so memory
latency, hit rates, and failure rates are fully observable.
"""

import logging
import time
from datetime import datetime, timezone

from bmasterai.logging import configure_logging, LogLevel, EventType

logger = logging.getLogger(__name__)

# Shared bmasterai logger — re-uses the instance created in agent/main.py
# if already configured; configure_logging() is idempotent.
bm = configure_logging(log_level=LogLevel.INFO, enable_console=False, enable_json=True)

_AGENT_ID = "agentcore-memory-agent"


class MemoryManager:
    """
    Thin wrapper around the bedrock-agentcore data-plane client
    for memory read/write operations.
    """

    def __init__(self, agentcore_data, memory_id: str):
        self._client = agentcore_data
        self._memory_id = memory_id

    # ------------------------------------------------------------------
    # Write: store a user ↔ assistant turn as an event
    # ------------------------------------------------------------------
    def store_turn(
        self,
        actor_id: str,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> dict:
        """
        Record a single conversation turn.
        AgentCore will asynchronously extract long-term memories
        (summaries, preferences, facts) from accumulated events.
        """
        t0 = time.monotonic()

        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.TOOL_USE,
            message="Storing conversation turn in AgentCore memory",
            metadata={
                "actor_id": actor_id,
                "session_id": session_id,
                "user_len": len(user_message),
                "assistant_len": len(assistant_message),
            },
        )

        try:
            response = self._client.create_event(
                memoryId=self._memory_id,
                actorId=actor_id,
                sessionId=session_id,
                eventTimestamp=datetime.now(timezone.utc),
                payload=[
                    {
                        "conversational": {
                            "role": "USER",
                            "content": {"text": user_message},
                        }
                    },
                    {
                        "conversational": {
                            "role": "ASSISTANT",
                            "content": {"text": assistant_message},
                        }
                    },
                ],
            )

            event_id = response.get("eventId", "unknown")
            duration_ms = (time.monotonic() - t0) * 1000

            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.TASK_COMPLETE,
                message=f"Memory turn stored — event_id={event_id}",
                metadata={
                    "actor_id": actor_id,
                    "session_id": session_id,
                    "event_id": event_id,
                },
                duration_ms=duration_ms,
            )

            logger.info(
                "Stored turn for actor=%s session=%s event_id=%s",
                actor_id,
                session_id,
                event_id,
            )
            return response

        except Exception as exc:
            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to store memory event: {exc}",
                metadata={"actor_id": actor_id, "session_id": session_id, "error": str(exc)},
            )
            logger.exception("Failed to store memory event")
            raise

    # ------------------------------------------------------------------
    # Read: retrieve relevant long-term memories
    # ------------------------------------------------------------------
    def retrieve(
        self,
        actor_id: str,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Semantic search across all memory strategies for this actor.
        Returns a list of memory records ranked by relevance.
        """
        t0 = time.monotonic()

        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.DECISION_POINT,
            message="Retrieving long-term memories from AgentCore",
            metadata={
                "actor_id": actor_id,
                "query_preview": query[:80],
                "max_results": max_results,
            },
        )

        try:
            response = self._client.retrieve_memory_records(
                memoryId=self._memory_id,
                query=query,
                actorId=actor_id,
                maxResults=max_results,
            )
            records = response.get("memoryRecords", [])
            duration_ms = (time.monotonic() - t0) * 1000

            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.PERFORMANCE_METRIC,
                message=f"Memory retrieval returned {len(records)} records",
                metadata={
                    "actor_id": actor_id,
                    "record_count": len(records),
                    "memory_types": list({r.get("memoryStrategyName", "unknown") for r in records}),
                },
                duration_ms=duration_ms,
            )

            logger.info(
                "Retrieved %d memories for actor=%s query='%s...'",
                len(records),
                actor_id,
                query[:50],
            )
            return records

        except Exception as exc:
            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.TASK_ERROR,
                message=f"Memory retrieval failed: {exc}",
                metadata={"actor_id": actor_id, "error": str(exc)},
            )
            logger.exception("Failed to retrieve memories")
            return []

    # ------------------------------------------------------------------
    # Session management helpers
    # ------------------------------------------------------------------
    def close_session(self, actor_id: str, session_id: str) -> None:
        """
        Signal that a session is complete so AgentCore can generate
        the session summary memory record.
        """
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.AGENT_COMMUNICATION,
            message="Closing session — signalling AgentCore for summary generation",
            metadata={"actor_id": actor_id, "session_id": session_id},
        )

        try:
            self._client.create_event(
                memoryId=self._memory_id,
                actorId=actor_id,
                sessionId=session_id,
                eventTimestamp=datetime.now(timezone.utc),
                payload=[
                    {
                        "conversational": {
                            "role": "SYSTEM",
                            "content": {"text": "[SESSION_ENDED]"},
                        }
                    }
                ],
            )
            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.TASK_COMPLETE,
                message="Session closed successfully",
                metadata={"actor_id": actor_id, "session_id": session_id},
            )
            logger.info("Closed session=%s for actor=%s", session_id, actor_id)

        except Exception as exc:
            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to close session: {exc}",
                metadata={"actor_id": actor_id, "session_id": session_id, "error": str(exc)},
            )
            logger.exception("Failed to close session")

    def delete_actor_memories(self, actor_id: str) -> None:
        """
        GDPR/privacy: delete all memories for a given actor.
        """
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.AGENT_COMMUNICATION,
            message="Deleting all memories for actor (GDPR request)",
            metadata={"actor_id": actor_id},
        )

        try:
            self._client.delete_memory_records(
                memoryId=self._memory_id,
                actorId=actor_id,
            )
            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.TASK_COMPLETE,
                message="Actor memories deleted",
                metadata={"actor_id": actor_id},
            )
            logger.info("Deleted all memories for actor=%s", actor_id)

        except Exception as exc:
            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to delete memories for actor={actor_id}: {exc}",
                metadata={"actor_id": actor_id, "error": str(exc)},
            )
            logger.exception("Failed to delete memories for actor=%s", actor_id)
