from bmasterai.logging import get_logger, EventType, LogLevel
from bmasterai.monitoring import get_monitor
import time
import uuid

class MyAgent:
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.status = "initialized"

        # Log agent creation
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"Agent {self.name} initialized",
            metadata={"name": self.name}
        )

    def start(self):
        self.status = "running"
        self.monitor.track_agent_start(self.agent_id)

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"Agent {self.name} started",
            level=LogLevel.INFO
        )

    def execute_task(self, task_name: str, task_data: dict = None):
        task_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Log task start
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Starting task: {task_name}",
                metadata={"task_id": task_id, "task_data": task_data or {}}
            )

            # Your custom task logic here
            result = self.custom_task(task_data or {})

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Track performance
            self.monitor.track_task_duration(self.agent_id, task_name, duration_ms)

            # Log task completion
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Completed task: {task_name}",
                metadata={"task_id": task_id, "duration_ms": duration_ms, "result": result},
                duration_ms=duration_ms
            )

            return {"success": True, "task_id": task_id, "result": result}

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Track error
            self.monitor.track_error(self.agent_id, "task_execution")

            # Log error
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Task failed: {task_name} - {str(e)}",
                level=LogLevel.ERROR,
                metadata={"task_id": task_id, "error": str(e)},
                duration_ms=duration_ms
            )

            return {"success": False, "error": str(e), "task_id": task_id}

    def custom_task(self, task_data: dict):
        """Implement your custom task logic here"""
        # Simulate some work
        time.sleep(1)
        return {"message": "Task completed successfully", "data": task_data}

    def stop(self):
        self.status = "stopped"
        self.monitor.track_agent_stop(self.agent_id)

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_STOP,
            f"Agent {self.name} stopped",
            level=LogLevel.INFO
        )

if __name__ == "__main__":
    agent = MyAgent("my-agent", "MyCustomAgent")
    agent.start()

    result = agent.execute_task("custom_task", {"data": "example"})
    print(f"Result: {result}")

    agent.stop()
