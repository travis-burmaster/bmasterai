# BMasterAI LLM Cost Analysis Telemetry Demo - Component Overview

This document provides a comprehensive overview of all components in the BMasterAI LLM cost analysis telemetry demo and how they work together to provide real-time monitoring of LLM usage and costs in a Kubernetes environment.

## Component Architecture

### 1. Custom Resource Definition (CRD)
**File**: `bmasterrun-crd.yaml`

The BMasterRun CRD defines a custom Kubernetes resource for tracking LLM runs with comprehensive telemetry data:

- **Spec Fields**:
  - `userId`: User identifier for the LLM run
  - `model`: LLM model used (e.g., gpt-4, claude-3-sonnet)
  - `namespace`: Environment context (production, staging, etc.)
  - `inputTokens`/`outputTokens`: Token consumption metrics
  - `costUsd`: Cost of the LLM run in USD
  - `tools`: List of tools used during the run
  - `maxTokens`, `temperature`, `topP`: LLM parameters

- **Status Fields**:
  - `phase`: Run status (Pending, Running, Succeeded, Failed)
  - `traceID`: OpenTelemetry trace identifier
  - `errorCount`: Number of errors encountered
  - `startTime`/`endTime`: Execution timestamps
  - `processingTimeMs`: Total processing time
  - `metadata`: Additional contextual information

### 2. Kubernetes Controller
**File**: `bmasterrun-controller.py`

The Kopf-based controller processes BMasterRun resources and generates telemetry data:

- Watches for BMasterRun resource creation/update/deletion
- Calculates costs based on model and token usage
- Updates resource status with execution metrics
- Simulates realistic processing times and error scenarios
- Integrates with OpenTelemetry for distributed tracing

### 3. OpenTelemetry Collector
**File**: `otel-collector-config.yaml`

Centralized telemetry collection and distribution:

- **Receivers**: Accepts OTLP data via gRPC and HTTP
- **Processors**: Batches, limits memory usage, and enriches data
- **Exporters**: 
  - Prometheus for metrics (token usage, costs, latency)
  - Loki for logs
  - Tempo for distributed traces
- **Extensions**: Health checks, profiling, and debugging endpoints

### 4. Data Generator
**File**: `generate-llm-runs.py`

Creates sample LLM run data for demonstration:

- Generates realistic token usage patterns
- Simulates different LLM models with appropriate pricing
- Creates varied error scenarios
- Populates all CRD fields with meaningful data

### 5. Grafana Dashboard
**File**: `bmasterai-dashboard.json`

Comprehensive visualization of LLM cost and performance metrics:

- **Token Usage**: Input/output tokens by model and namespace
- **Cost Analysis**: Real-time and cumulative costs by model
- **Performance**: Latency metrics and processing times
- **Error Monitoring**: Error rates and failure patterns
- **Efficiency**: Token efficiency ratios and model comparisons
- **Trace Links**: Direct access to detailed distributed traces

## Data Flow

1. **Data Generation**: 
   - Sample LLM runs created via `generate-llm-runs.py`
   - Resources stored as BMasterRun custom resources in Kubernetes

2. **Controller Processing**:
   - Controller watches for new BMasterRun resources
   - Enriches resources with execution metrics and costs
   - Updates resource status with telemetry data

3. **Telemetry Collection**:
   - Controller emits OTLP metrics, logs, and traces
   - OpenTelemetry Collector receives and processes telemetry data
   - Data routed to appropriate backends (Prometheus, Loki, Tempo)

4. **Data Storage**:
   - Metrics stored in Prometheus time-series database
   - Logs stored in Loki
   - Traces stored in Tempo

5. **Visualization**:
   - Grafana queries Prometheus for metrics
   - Dashboard displays real-time LLM cost and performance data
   - Users can drill down into traces via Tempo integration

## Key Metrics Tracked

### Cost Metrics
- Real-time cost per model/namespace
- Cumulative cost by model
- Cost efficiency comparisons

### Performance Metrics
- Latency percentiles (P95, P99)
- Processing time distributions
- Token processing rates

### Quality Metrics
- Error rates by model/namespace
- Success/failure ratios
- Retry patterns

### Usage Metrics
- Token consumption (input/output)
- Tool utilization
- Model distribution

## Demo Workflow

1. **Setup**: Deploy all components to a local Kubernetes cluster
2. **Data Generation**: Create sample LLM runs with varying parameters
3. **Processing**: Controller enriches runs with telemetry data
4. **Collection**: OpenTelemetry Collector processes and routes telemetry
5. **Visualization**: View real-time metrics in Grafana dashboard
6. **Analysis**: Examine cost patterns, performance bottlenecks, and error trends

## Customization Points

### Model Pricing
Update the pricing dictionary in both controller and data generator to reflect actual LLM pricing:

```python
pricing = {
    'gpt-4': {'input': 0.03/1000, 'output': 0.06/1000},
    'gpt-3.5-turbo': {'input': 0.0015/1000, 'output': 0.002/1000},
    # Add new models here
}
```

### Dashboard Panels
Modify the Grafana dashboard JSON to add new visualizations or adjust existing ones.

### Alerting
Add Prometheus alerting rules for cost thresholds, error rates, or performance SLAs.

This comprehensive telemetry system provides real-time visibility into LLM usage patterns, costs, and performance, enabling data-driven optimization of AI workloads in Kubernetes environments.