# BMasterAI LLM Cost Analysis Telemetry Demo

This example demonstrates how to set up Kubernetes-native observability for BMasterAI with a focus on LLM cost analysis using OpenTelemetry, Grafana, Prometheus, Loki, and Tempo.

## Overview

This demo showcases:
- Real-time LLM cost tracking by model
- Token usage monitoring
- Performance metrics and error rates
- Distributed tracing for LLM workflows
- Custom Kubernetes resources for LLM run tracking

## Prerequisites

1. Docker Desktop with Kubernetes enabled OR a local Kubernetes cluster (minikube, kind, etc.)
2. kubectl installed and configured
3. Helm 3.x installed
4. Python 3.8+ with pip

## Included Files

- `bmasterrun-crd.yaml`: Kubernetes Custom Resource Definition for BMasterRun resource
- `otel-collector-config.yaml`: OpenTelemetry Collector configuration for routing traces, logs, and metrics
- `bmasterai-dashboard.json`: Grafana dashboard JSON for LLM cost analysis, token usage, latency, and trace links
- `bmasterrun-controller.py`: Kopf-based Kubernetes controller for BMasterRun resources
- `generate-llm-runs.py`: Sample data generator for creating LLM run instances

## Complete Setup Instructions

### 1. Create Observability Namespace

```bash
kubectl create namespace observability
```

### 2. Install Observability Stack

#### Install Prometheus using Helm

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus -n observability
```

#### Install Grafana using Helm

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana -n observability
```

#### Install Loki for Logs

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki -n observability
```

#### Install Tempo for Distributed Tracing

```bash
helm install tempo grafana/tempo -n observability
```

### 3. Deploy OpenTelemetry Collector

```bash
# Apply the OpenTelemetry collector configuration
kubectl apply -f otel-collector-config.yaml

# Deploy the OpenTelemetry collector
kubectl apply -f https://github.com/open-telemetry/opentelemetry-collector/releases/latest/download/opentelemetry-collector-k8s.yaml
```

### 4. Deploy BMasterAI Telemetry Components

```bash
# Apply the Custom Resource Definition
kubectl apply -f bmasterrun-crd.yaml

# Verify the CRD was created
kubectl get crd bmasterruns.bmasterai.ai
```

### 5. Create Sample BMasterRun Resources

```bash
# Create a few sample BMasterRun resources
kubectl apply -f - <<EOF
apiVersion: bmasterai.ai/v1alpha1
kind: BMasterRun
metadata:
  name: sample-gpt4-run
  namespace: observability
spec:
  userId: "user-123"
  model: "gpt-4"
  namespace: "production"
  inputTokens: 500
  outputTokens: 300
  costUsd: 0.048
  tools: ["web_search", "code_execution"]
EOF

kubectl apply -f - <<EOF
apiVersion: bmasterai.ai/v1alpha1
kind: BMasterRun
metadata:
  name: sample-claude-run
  namespace: observability
spec:
  userId: "user-456"
  model: "claude-3-sonnet"
  namespace: "staging"
  inputTokens: 300
  outputTokens: 200
  costUsd: 0.0039
  tools: ["web_search"]
EOF
```

### 6. Run the Controller

In a separate terminal, run the BMasterRun controller:

```bash
# Install required Python dependencies
pip install kopf kubernetes

# Run the controller in standalone mode
kopf run bmasterrun-controller.py --standalone --standalone --verbose
```

### 7. Generate Sample Data (Optional)

To generate more sample LLM runs for demonstration:

```bash
# Create generate-llm-runs.py if it doesn't exist
cat > generate-llm-runs.py << 'EOF'
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
EOF

# Run the sample data generator
python generate-llm-runs.py
```

### 8. View in Grafana

1. Get the Grafana admin password:
   ```bash
   kubectl get secret --namespace observability grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
   ```

2. Port forward Grafana to access it locally:
   ```bash
   kubectl port-forward svc/grafana 3000:80 -n observability
   ```

3. Open your browser and navigate to http://localhost:3000

4. Log in with username `admin` and the password retrieved in step 1

5. Import the BMasterAI dashboard:
   - Click the "+" icon in the left sidebar
   - Select "Import"
   - Upload the `bmasterai-dashboard.json` file or paste its contents
   - Select Prometheus as the data source
   - Click "Import"

## Expected Dashboard Results

The BMasterAI dashboard will display:

1. **Tokens per Model/Namespace**: Table showing token usage by model and namespace
2. **LLM Cost Analysis**: Visualization of costs by model in USD
3. **Latency Metrics**: Response time measurements for LLM operations
4. **Trace Links**: Links to detailed distributed traces in Tempo
5. **Error Rates**: Metrics on failed LLM requests
6. **Token Efficiency**: Ratio of output tokens to input tokens

## Troubleshooting

### Common Issues

1. **Controller fails to start**:
   - Ensure kubectl is properly configured
   - Verify the CRD was applied successfully
   - Check RBAC permissions

2. **No data in Grafana**:
   - Verify the OpenTelemetry collector is running
   - Check that the controller is processing BMasterRun resources
   - Ensure Prometheus is scraping the correct endpoints

3. **Cannot access Grafana**:
   - Verify the port-forward command is still running
   - Check that Grafana pod is running:
     ```bash
     kubectl get pods -n observability
     ```

### Useful Commands

```bash
# Check BMasterRun resources
kubectl get bmasterruns -n observability

# Describe a specific BMasterRun
kubectl describe bmasterrun sample-gpt4-run -n observability

# Check controller logs
kubectl logs -f <controller-pod-name> -n observability

# Check OpenTelemetry collector logs
kubectl logs -f <otel-collector-pod-name> -n observability

# Verify all services are running
kubectl get svc -n observability
```

## Customization

### Adding New Models

To add support for new LLM models, update the pricing dictionary in both the controller and data generator:

```python
# In bmasterrun-controller.py and generate-llm-runs.py
pricing = {
    'gpt-4': {'input': 0.03/1000, 'output': 0.06/1000},
    'gpt-3.5-turbo': {'input': 0.0015/1000, 'output': 0.002/1000},
    'claude-3-opus': {'input': 0.015/1000, 'output': 0.075/1000},
    'claude-3-sonnet': {'input': 0.003/1000, 'output': 0.015/1000},
    'new-model': {'input': 0.01/1000, 'output': 0.02/1000},  # Add new model here
}
```

### Modifying the Dashboard

To customize the Grafana dashboard:
1. Open the dashboard in Grafana
2. Click the gear icon (Dashboard settings)
3. Select "JSON Model"
4. Modify the JSON as needed
5. Save and reload the dashboard

## Architecture Overview

This telemetry system follows a cloud-native architecture:

1. **Data Source**: BMasterRun custom resources represent LLM operations
2. **Controller**: Kopf-based controller processes BMasterRun resources and generates metrics
3. **Collection**: OpenTelemetry collector gathers metrics, logs, and traces
4. **Storage**: Prometheus (metrics), Loki (logs), Tempo (traces)
5. **Visualization**: Grafana dashboard for real-time monitoring

## Security Considerations

For production use, consider:
- Implementing proper RBAC for the controller
- Using TLS for all service communications
- Securing Grafana with proper authentication
- Limiting access to sensitive metrics
- Regularly rotating API keys and credentials

## Next Steps

To extend this demo:
1. Integrate with actual LLM APIs to collect real usage data
2. Add alerting rules for cost thresholds
3. Implement log aggregation for detailed debugging
4. Add more detailed tracing for complex workflows
5. Create automated reports for cost analysis

This example provides a solid foundation for monitoring LLM costs and performance in Kubernetes environments.