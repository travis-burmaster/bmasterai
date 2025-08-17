import kopf
import kubernetes.client
from kubernetes.client.rest import ApiException
import time
import random
from datetime import datetime

# Enhanced Kubernetes controller for BMasterRun resources with LLM cost analysis

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = 10  # DEBUG

@kopf.on.create('bmasterai.ai', 'v1alpha1', 'bmasterruns')
def on_bmasterrun_create(spec, status, namespace, name, logger, **kwargs):
    logger.info(f"BMasterRun created: {name} in {namespace}")
    
    # Extract LLM run details
    model = spec.get('model', 'gpt-4')
    input_tokens = spec.get('inputTokens', 0)
    output_tokens = spec.get('outputTokens', 0)
    cost_usd = spec.get('costUsd', 0.0)
    user_id = spec.get('userId', 'unknown')
    tools = spec.get('tools', [])
    
    # If cost is not provided, calculate it based on model and tokens
    if cost_usd == 0.0 and input_tokens > 0 and output_tokens > 0:
        cost_usd = calculate_cost(model, input_tokens, output_tokens)
    
    # Simulate processing time
    processing_time_ms = random.randint(100, 5000)
    
    # Randomly determine if there was an error (5% chance)
    has_error = random.random() < 0.05
    error_count = 1 if has_error else 0
    
    api = kubernetes.client.CustomObjectsApi()
    try:
        # Update with realistic telemetry data
        status_update = {
            "status": {
                "phase": "Failed" if has_error else "Succeeded",
                "traceID": f"trace-{int(time.time()*1000000)}",
                "errorCount": error_count,
                "startTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "processingTimeMs": processing_time_ms,
                "costUsd": round(cost_usd, 6),
                "metadata": {
                    "userId": user_id,
                    "toolsUsed": tools
                }
            }
        }
        
        api.patch_namespaced_custom_object_status(
            group="bmasterai.ai",
            version="v1alpha1",
            namespace=namespace,
            plural="bmasterruns",
            name=name,
            body=status_update,
        )
        logger.info(f"Updated status for BMasterRun {name} with cost ${cost_usd}")
    except ApiException as e:
        logger.error(f"Failed to update status for BMasterRun {name}: {e}")

@kopf.on.update('bmasterai.ai', 'v1alpha1', 'bmasterruns')
def on_bmasterrun_update(spec, status, namespace, name, logger, **kwargs):
    logger.info(f"BMasterRun updated: {name} in {namespace}")
    
    # Here you could add logic to update status based on external data
    # For demo purposes, we'll just log the update
    logger.info(f"Spec updated: {spec}")

@kopf.on.delete('bmasterai.ai', 'v1alpha1', 'bmasterruns')
def on_bmasterrun_delete(spec, status, namespace, name, logger, **kwargs):
    logger.info(f"BMasterRun deleted: {name} in {namespace}")
    
    # Log deletion for audit purposes
    logger.info(f"LLM run {name} for user {spec.get('userId', 'unknown')} was deleted")

def calculate_cost(model, input_tokens, output_tokens):
    """Calculate approximate cost based on model and token usage"""
    # Simplified pricing (real implementation would use actual API pricing)
    pricing = {
        'gpt-4': {'input': 0.03/1000, 'output': 0.06/1000},
        'gpt-3.5-turbo': {'input': 0.0015/1000, 'output': 0.002/1000},
        'claude-3-opus': {'input': 0.015/1000, 'output': 0.075/1000},
        'claude-3-sonnet': {'input': 0.003/1000, 'output': 0.015/1000},
    }
    
    model_pricing = pricing.get(model, pricing['gpt-4'])
    return (input_tokens * model_pricing['input']) + (output_tokens * model_pricing['output'])

# To run this controller:
# 1. Install kopf: pip install kopf kubernetes
# 2. Run: kopf run bmasterrun-controller.py --standalone --verbose