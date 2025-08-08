"""
Cost Monitoring with OpenTelemetry and Agno

This example demonstrates advanced cost monitoring for AI agents using:
- Agno framework for agent orchestration
- BMasterAI for telemetry and cost tracking
- OpenTelemetry for distributed tracing
- Real-time cost alerts and budget management

This shows how to build production-ready AI agents with comprehensive
cost visibility and automated budget controls.
"""

import os
import time
from decimal import Decimal
from typing import Dict, List

from agno.agent import Agent
from agno.models.google import Gemini

from bmasterai.logging import configure_logging, LogLevel, EventType
from bmasterai.monitoring import get_monitor
from bmasterai_telemetry.alerts.slack import build_slack_alert, send_slack_alert
from bmasterai_telemetry.alerts.teams import send_teams_alert

# OpenTelemetry imports for distributed tracing
try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    print("⚠️  OpenTelemetry not installed. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger opentelemetry-instrumentation-requests")
    OTEL_AVAILABLE = False


class CostTracker:
    """Advanced cost tracking with budget management and alerting."""
    
    def __init__(self):
        self.costs: Dict[str, Decimal] = {}
        self.budgets: Dict[str, Decimal] = {}
        self.model_costs = {
            "gemini-1.5-flash": {"input": Decimal("0.000075"), "output": Decimal("0.0003")},  # per 1K tokens
            "gemini-1.5-pro": {"input": Decimal("0.00125"), "output": Decimal("0.005")},
        }
    
    def set_budget(self, agent_id: str, budget: Decimal):
        """Set budget limit for an agent."""
        self.budgets[agent_id] = budget
        print(f"💰 Budget set for {agent_id}: ${budget}")
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost based on token usage."""
        if model not in self.model_costs:
            return Decimal("0")
        
        costs = self.model_costs[model]
        input_cost = (Decimal(input_tokens) / 1000) * costs["input"]
        output_cost = (Decimal(output_tokens) / 1000) * costs["output"]
        return input_cost + output_cost
    
    def track_cost(self, agent_id: str, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Track cost for an agent and check budget."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        if agent_id not in self.costs:
            self.costs[agent_id] = Decimal("0")
        
        self.costs[agent_id] += cost
        total_cost = self.costs[agent_id]
        
        print(f"💸 Cost for {agent_id}: +${cost:.6f} (total: ${total_cost:.6f})")
        
        # Check budget
        if agent_id in self.budgets and total_cost > self.budgets[agent_id]:
            self._send_budget_alert(agent_id, total_cost, self.budgets[agent_id])
        
        return cost
    
    def _send_budget_alert(self, agent_id: str, current_cost: Decimal, budget: Decimal):
        """Send budget breach alert."""
        alert_text = (
            f"🚨 Budget breach for agent {agent_id}: "
            f"${current_cost:.2f} used > ${budget:.2f} limit"
        )
        dashboard_url = os.getenv("BMASTERAI_DASHBOARD_URL", "http://localhost:3000/d/agent-dashboard")
        
        print(f"🚨 {alert_text}")
        
        # Send alerts
        send_slack_alert(build_slack_alert(alert_text, dashboard_url))
        send_teams_alert(agent_id, alert_text, dashboard_url)


def setup_opentelemetry():
    """Configure OpenTelemetry for distributed tracing."""
    if not OTEL_AVAILABLE:
        return None
    
    # Set up tracing
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure Jaeger exporter (optional)
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=14268,
    )
    
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument HTTP requests
    RequestsInstrumentor().instrument()
    
    print("🔍 OpenTelemetry tracing configured")
    return tracer


def run_cost_monitoring_example():
    """Run the cost monitoring example with multiple agents."""
    
    # Setup
    logger = configure_logging(log_level=LogLevel.INFO, enable_console=True)
    monitor = get_monitor()
    monitor.start_monitoring()
    
    cost_tracker = CostTracker()
    tracer = setup_opentelemetry()
    
    # Create multiple agents with different budgets
    agents_config = [
        {"id": "research-agent", "budget": Decimal("5.00"), "prompt": "Research the latest developments in AI observability and write a summary."},
        {"id": "creative-agent", "budget": Decimal("2.00"), "prompt": "Write a creative story about an AI agent that becomes self-aware of its costs."},
        {"id": "analysis-agent", "budget": Decimal("3.00"), "prompt": "Analyze the importance of cost monitoring in production AI systems."},
    ]
    
    for agent_config in agents_config:
        agent_id = agent_config["id"]
        budget = agent_config["budget"]
        prompt = agent_config["prompt"]
        
        # Set budget
        cost_tracker.set_budget(agent_id, budget)
        
        # Start tracing span
        if tracer:
            with tracer.start_as_current_span(f"agent-execution-{agent_id}") as span:
                span.set_attribute("agent.id", agent_id)
                span.set_attribute("agent.budget", float(budget))
                run_agent_with_monitoring(agent_id, prompt, cost_tracker, logger, monitor, span)
        else:
            run_agent_with_monitoring(agent_id, prompt, cost_tracker, logger, monitor)
    
    # Summary
    print("\n" + "="*60)
    print("💰 COST SUMMARY")
    print("="*60)
    total_cost = Decimal("0")
    for agent_id, cost in cost_tracker.costs.items():
        budget = cost_tracker.budgets.get(agent_id, Decimal("0"))
        status = "🚨 OVER BUDGET" if cost > budget else "✅ Within budget"
        print(f"{agent_id:20} ${cost:8.6f} / ${budget:6.2f} {status}")
        total_cost += cost
    
    print("-" * 60)
    print(f"{'TOTAL COST':20} ${total_cost:8.6f}")
    print("="*60)


def run_agent_with_monitoring(agent_id: str, prompt: str, cost_tracker: CostTracker, 
                            logger, monitor, span=None):
    """Run a single agent with comprehensive monitoring."""
    
    print(f"\n🤖 Starting agent: {agent_id}")
    monitor.track_agent_start(agent_id)
    
    if span:
        span.add_event("agent.started")
    
    # Create Agno agent
    agent = Agent(
        model=Gemini(id="gemini-1.5-flash", api_key=os.environ.get("GOOGLE_API_KEY")),
        markdown=True,
        description=f"Agent {agent_id} with cost monitoring",
    )
    
    try:
        start_time = time.time()
        response = agent.run(prompt)
        duration_ms = (time.time() - start_time) * 1000
        
        # Extract token usage
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        
        raw = getattr(response, "raw_response", None)
        if raw is not None:
            usage = getattr(raw, "usage_metadata", None)
            if usage:
                input_tokens = getattr(usage, "prompt_token_count", 0)
                output_tokens = getattr(usage, "candidates_token_count", 0)
                total_tokens = getattr(usage, "total_token_count", 0)
        
        # Track costs
        cost = cost_tracker.track_cost(agent_id, "gemini-1.5-flash", input_tokens, output_tokens)
        
        # Record metrics
        monitor.track_llm_call(agent_id, "gemini-1.5-flash", total_tokens, duration_ms)
        logger.log_event(
            agent_id=agent_id,
            event_type=EventType.LLM_CALL,
            message="LLM call completed with cost tracking",
            metadata={
                "tokens_used": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": float(cost),
                "model": "gemini-1.5-flash"
            },
            duration_ms=duration_ms,
        )
        
        if span:
            span.set_attribute("llm.tokens.input", input_tokens)
            span.set_attribute("llm.tokens.output", output_tokens)
            span.set_attribute("llm.tokens.total", total_tokens)
            span.set_attribute("llm.cost.usd", float(cost))
            span.set_attribute("llm.duration.ms", duration_ms)
            span.add_event("llm.call.completed")
        
        print(f"📝 Response preview: {response.content[:100]}...")
        
    except Exception as e:
        error_msg = f"Error in agent {agent_id}: {str(e)}"
        print(f"❌ {error_msg}")
        logger.log_event(
            agent_id=agent_id,
            event_type=EventType.ERROR,
            message=error_msg,
        )
        if span:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
    
    finally:
        monitor.track_agent_stop(agent_id)
        logger.log_event(
            agent_id=agent_id,
            event_type=EventType.AGENT_STOP,
            message=f"Agent {agent_id} completed",
        )
        if span:
            span.add_event("agent.stopped")


if __name__ == "__main__":
    print("🚀 Starting Cost Monitoring with OpenTelemetry and Agno Example")
    print("=" * 60)
    
    # Check for required environment variables
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY environment variable is required")
        exit(1)
    
    run_cost_monitoring_example()
