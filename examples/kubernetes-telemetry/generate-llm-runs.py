import kubernetes.client
from kubernetes.client.rest import ApiException
import random
import time

def create_sample_llm_runs():
    api = kubernetes.client.CustomObjectsApi()
    
    models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet']
    
    for i in range(10):
        model = random.choice(models)
        input_tokens = random.randint(100, 2000)
        output_tokens = random.randint(50, 1000)
        
        # Calculate approximate cost based on model and tokens
        pricing = {
            'gpt-4': {'input': 0.03/1000, 'output': 0.06/1000},
            'gpt-3.5-turbo': {'input': 0.0015/1000, 'output': 0.002/1000},
            'claude-3-opus': {'input': 0.015/1000, 'output': 0.075/1000},
            'claude-3-sonnet': {'input': 0.003/1000, 'output': 0.015/1000},
        }
        
        model_pricing = pricing.get(model, pricing['gpt-4'])
        cost_usd = (input_tokens * model_pricing['input']) + (output_tokens * model_pricing['output'])
        
        bmasterrun = {
            "apiVersion": "bmasterai.ai/v1alpha1",
            "kind": "BMasterRun",
            "metadata": {
                "name": f"llm-run-{i}-{int(time.time())}",
                "namespace": "observability"
            },
            "spec": {
                "userId": f"user-{random.randint(1, 100)}",
                "model": model,
                "namespace": random.choice(["production", "staging", "development"]),
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "costUsd": round(cost_usd, 6),
                "tools": random.sample(["web_search", "code_execution", "file_access", "api_call"], 
                                     random.randint(1, 3))
            }
        }
        
        try:
            api.create_namespaced_custom_object(
                group="bmasterai.ai",
                version="v1alpha1",
                namespace="observability",
                plural="bmasterruns",
                body=bmasterrun,
            )
            print(f"Created BMasterRun: llm-run-{i}")
            time.sleep(0.5)  # Small delay between creations
        except ApiException as e:
            print(f"Exception when creating BMasterRun: {e}")

if __name__ == "__main__":
    create_sample_llm_runs()