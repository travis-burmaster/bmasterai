# Kubernetes Deployment Guide

This comprehensive guide covers deploying BMasterAI on Kubernetes clusters, including Amazon EKS, Google GKE, and Azure AKS. Whether you're deploying for development, staging, or production, this guide provides step-by-step instructions and best practices.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Cloud Provider Specifics](#cloud-provider-specifics)
- [Deployment Methods](#deployment-methods)
- [Configuration](#configuration)
- [Monitoring and Observability](#monitoring-and-observability)
- [Security](#security)
- [Scaling and Performance](#scaling-and-performance)
- [Troubleshooting](#troubleshooting)
- [Production Considerations](#production-considerations)

## Prerequisites

### Required Tools

- **kubectl** (v1.25+): Kubernetes command-line tool
- **Helm** (v3.8+): Package manager for Kubernetes
- **Docker**: For building custom images (optional)

### Cloud Provider CLI Tools

**Amazon EKS:**
```bash
# Install AWS CLI and eksctl
aws --version
eksctl version
```

**Google GKE:**
```bash
# Install gcloud SDK
gcloud version
```

**Azure AKS:**
```bash
# Install Azure CLI
az version
```

### Minimum Cluster Requirements

- **Kubernetes Version**: 1.25+
- **Nodes**: 2+ worker nodes
- **CPU**: 2+ cores per node
- **Memory**: 4GB+ RAM per node
- **Storage**: 20GB+ available storage

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
```

### 2. Create Cluster (Choose Your Platform)

**Amazon EKS:**
```bash
eksctl create cluster --config-file=eks/cluster-config.yaml
```

**Google GKE:**
```bash
gcloud container clusters create bmasterai-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-standard-2
```

**Azure AKS:**
```bash
az aks create \
  --resource-group myResourceGroup \
  --name bmasterai-cluster \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3
```

### 3. Deploy BMasterAI

**Using Helm (Recommended):**
```bash
# Create namespace
kubectl create namespace bmasterai

# Install BMasterAI
helm install bmasterai ./helm/bmasterai \
  --namespace bmasterai \
  --set secrets.openaiApiKey=$(echo -n "your-api-key" | base64)
```

**Using kubectl:**
```bash
# Apply all manifests
kubectl apply -f k8s/
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n bmasterai

# Check service endpoints
kubectl get services -n bmasterai

# View logs
kubectl logs -f deployment/bmasterai-agent -n bmasterai
```

## Cloud Provider Specifics

### Amazon EKS

#### IAM Configuration

Create IAM policy for BMasterAI:
```bash
aws iam create-policy \
  --policy-name BMasterAIPolicy \
  --policy-document file://eks/aws-iam-policy.json
```

Enable IRSA (IAM Roles for Service Accounts):
```bash
eksctl create iamserviceaccount \
  --cluster=bmasterai-cluster \
  --namespace=bmasterai \
  --name=bmasterai-service-account \
  --attach-policy-arn=arn:aws:iam::ACCOUNT:policy/BMasterAIPolicy \
  --approve
```

#### EBS CSI Driver

Install EBS CSI driver for persistent volumes:
```bash
eksctl create addon --name aws-ebs-csi-driver --cluster bmasterai-cluster
```

#### Load Balancer Controller

Install AWS Load Balancer Controller:
```bash
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=bmasterai-cluster
```

### Google GKE

#### Enable Required APIs

```bash
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
```

#### Workload Identity

Enable Workload Identity for secure access:
```bash
gcloud container clusters update bmasterai-cluster \
  --workload-pool=PROJECT_ID.svc.id.goog
```

#### GKE Autopilot

For managed experience, use GKE Autopilot:
```bash
gcloud container clusters create-auto bmasterai-autopilot \
  --region=us-central1
```

### Azure AKS

#### Enable Add-ons

```bash
# Enable monitoring add-on
az aks enable-addons \
  --resource-group myResourceGroup \
  --name bmasterai-cluster \
  --addons monitoring
```

#### Azure AD Integration

```bash
# Enable Azure AD integration
az aks update \
  --resource-group myResourceGroup \
  --name bmasterai-cluster \
  --enable-aad \
  --aad-admin-group-object-ids GROUP_ID
```

## Deployment Methods

### Method 1: Helm Chart (Recommended)

#### Install BMasterAI

```bash
# Add custom values
cat > values-production.yaml << EOF
replicaCount: 3

image:
  repository: bmasterai
  tag: "latest"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10

persistence:
  enabled: true
  size: 10Gi

secrets:
  openaiApiKey: "eW91ci1hcGkta2V5"  # base64 encoded
  anthropicApiKey: "eW91ci1hbnRocm9waWMta2V5"
EOF

# Deploy with custom values
helm install bmasterai ./helm/bmasterai \
  --namespace bmasterai \
  --values values-production.yaml
```

#### Upgrade Deployment

```bash
# Upgrade to new version
helm upgrade bmasterai ./helm/bmasterai \
  --namespace bmasterai \
  --set image.tag=v1.2.0
```

#### Rollback Deployment

```bash
# View release history
helm history bmasterai -n bmasterai

# Rollback to previous version
helm rollback bmasterai 1 -n bmasterai
```

### Method 2: kubectl Manifests

#### Prepare Secrets

```bash
# Create secrets manually
kubectl create secret generic bmasterai-secrets \
  --from-literal=OPENAI_API_KEY=your-openai-key \
  --from-literal=ANTHROPIC_API_KEY=your-anthropic-key \
  --from-literal=SLACK_WEBHOOK_URL=your-slack-webhook \
  --namespace bmasterai
```

#### Deploy Components

```bash
# Deploy in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/service-account.yaml
kubectl apply -f k8s/persistent-volume.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/monitoring.yaml
```

### Method 3: Kustomize

Create `kustomization.yaml`:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: bmasterai

resources:
  - k8s/namespace.yaml
  - k8s/configmap.yaml
  - k8s/deployment.yaml
  - k8s/service.yaml
  - k8s/hpa.yaml

patchesStrategicMerge:
  - patches/production-patch.yaml

images:
  - name: bmasterai
    newTag: v1.2.0
```

Deploy with Kustomize:
```bash
kubectl apply -k .
```

## Configuration

### Environment Variables

Configure BMasterAI through environment variables:

```yaml
env:
  - name: LOG_LEVEL
    value: "INFO"
  - name: METRICS_ENABLED
    value: "true"
  - name: PROMETHEUS_PORT
    value: "9090"
  - name: WORKER_THREADS
    value: "4"
  - name: CACHE_SIZE
    value: "1000"
```

### ConfigMap Configuration

Update `k8s/configmap.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bmasterai-config
  namespace: bmasterai
data:
  config.yaml: |
    server:
      port: 8080
      host: "0.0.0.0"
    
    logging:
      level: "INFO"
      format: "json"
    
    monitoring:
      enabled: true
      prometheus:
        port: 9090
        path: "/metrics"
    
    performance:
      worker_threads: 4
      max_connections: 100
      timeout_seconds: 30
```

### Secrets Management

#### Option 1: Kubernetes Secrets

```bash
kubectl create secret generic bmasterai-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-... \
  --from-literal=DATABASE_URL=postgresql://... \
  --namespace bmasterai
```

#### Option 2: External Secrets Operator

Install External Secrets Operator:
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

Create SecretStore for AWS Secrets Manager:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: bmasterai
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        serviceAccount:
          name: bmasterai-service-account
```

#### Option 3: Vault Integration

Install Vault Injector:
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault -n vault --create-namespace
```

## Monitoring and Observability

### Prometheus Metrics

BMasterAI exposes metrics on `/metrics` endpoint:

```bash
# Port forward to access metrics
kubectl port-forward svc/bmasterai-service 8080:80 -n bmasterai
curl http://localhost:8080/metrics
```

### Install Prometheus Stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123
```

### Custom ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: bmasterai-metrics
  namespace: bmasterai
spec:
  selector:
    matchLabels:
      app: bmasterai
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Grafana Dashboards

Access Grafana:
```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

Import BMasterAI dashboard:
- Dashboard ID: Custom BMasterAI dashboard
- Key metrics: Request rate, error rate, response time, resource usage

### Logging

#### Enable JSON Logging

Set environment variable:
```yaml
env:
  - name: LOG_FORMAT
    value: "json"
```

#### ELK Stack Integration

Deploy Elasticsearch and Kibana:
```bash
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch -n logging --create-namespace
helm install kibana elastic/kibana -n logging
```

#### Fluent Bit for Log Collection

```bash
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluent-bit fluent/fluent-bit \
  --namespace logging \
  --set config.outputs='[OUTPUT]\n    Name es\n    Match *\n    Host elasticsearch-master\n    Port 9200'
```

### Distributed Tracing

#### Jaeger Installation

```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger -n tracing --create-namespace
```

#### OpenTelemetry Configuration

```yaml
env:
  - name: OTEL_EXPORTER_JAEGER_ENDPOINT
    value: "http://jaeger-collector:14268/api/traces"
  - name: OTEL_SERVICE_NAME
    value: "bmasterai"
```

## Security

### Pod Security Standards

Enable Pod Security Standards:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: bmasterai
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Network Policies

Create network policy:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: bmasterai-netpol
  namespace: bmasterai
spec:
  podSelector:
    matchLabels:
      app: bmasterai
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

### RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: bmasterai
  name: bmasterai-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: bmasterai-rolebinding
  namespace: bmasterai
subjects:
- kind: ServiceAccount
  name: bmasterai-service-account
  namespace: bmasterai
roleRef:
  kind: Role
  name: bmasterai-role
  apiGroup: rbac.authorization.k8s.io
```

### Image Scanning

#### Trivy Scanner

```bash
# Install Trivy operator
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/trivy-operator/main/deploy/static/trivy-operator.yaml

# Scan BMasterAI image
trivy image bmasterai:latest
```

#### OPA Gatekeeper

Install Gatekeeper:
```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml
```

Create security policies:
```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: requiresecuritycontext
spec:
  crd:
    spec:
      names:
        kind: RequireSecurityContext
      validation:
        openAPIV3Schema:
          type: object
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package requiresecuritycontext
        
        violation[{"msg": msg}] {
          not input.review.object.spec.securityContext.runAsNonRoot
          msg := "Containers must run as non-root user"
        }
```

## Scaling and Performance

### Horizontal Pod Autoscaler (HPA)

Configure HPA with custom metrics:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bmasterai-hpa
  namespace: bmasterai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bmasterai-agent
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "10"
```

### Vertical Pod Autoscaler (VPA)

Install VPA:
```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-install.sh
```

Configure VPA:
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: bmasterai-vpa
  namespace: bmasterai
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bmasterai-agent
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: bmasterai
      maxAllowed:
        cpu: 2
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

### Cluster Autoscaler

#### AWS EKS

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

kubectl -n kube-system annotate deployment.apps/cluster-autoscaler cluster-autoscaler.kubernetes.io/safe-to-evict="false"
```

#### GKE

```bash
gcloud container clusters update bmasterai-cluster \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

### Performance Tuning

#### Resource Limits and Requests

```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

#### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: bmasterai-pdb
  namespace: bmasterai
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: bmasterai
```

#### Node Affinity

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node-type
          operator: In
          values:
          - compute-optimized
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - bmasterai
        topologyKey: kubernetes.io/hostname
```

## Troubleshooting

### Common Issues

#### 1. Pod Startup Failures

```bash
# Check pod status
kubectl describe pod <pod-name> -n bmasterai

# View pod logs
kubectl logs <pod-name> -n bmasterai --previous

# Check events
kubectl get events -n bmasterai --sort-by='.lastTimestamp'
```

#### 2. Resource Constraints

```bash
# Check node resources
kubectl top nodes

# Check pod resources
kubectl top pods -n bmasterai

# Check resource quotas
kubectl describe resourcequota -n bmasterai
```

#### 3. Network Connectivity

```bash
# Test DNS resolution
kubectl exec -it <pod-name> -n bmasterai -- nslookup kubernetes.default

# Test external connectivity
kubectl exec -it <pod-name> -n bmasterai -- curl -I https://api.openai.com

# Check network policies
kubectl get networkpolicies -n bmasterai
```

#### 4. Storage Issues

```bash
# Check persistent volumes
kubectl get pv,pvc -n bmasterai

# Describe storage class
kubectl describe storageclass

# Check disk usage
kubectl exec -it <pod-name> -n bmasterai -- df -h
```

#### 5. Service Discovery

```bash
# Test service endpoints
kubectl get endpoints -n bmasterai

# Port forward for testing
kubectl port-forward svc/bmasterai-service 8080:80 -n bmasterai

# Check ingress configuration
kubectl describe ingress -n bmasterai
```

### Debugging Commands

```bash
# Interactive shell in pod
kubectl exec -it deployment/bmasterai-agent -n bmasterai -- /bin/bash

# Copy files from pod
kubectl cp bmasterai/pod-name:/app/logs/error.log ./error.log

# Check pod restart count
kubectl get pods -n bmasterai -o wide

# View resource usage over time
kubectl top pods -n bmasterai --containers
```

### Performance Debugging

```bash
# Check HPA status
kubectl describe hpa bmasterai-hpa -n bmasterai

# View custom metrics
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1" | jq .

# Check cluster autoscaler logs
kubectl logs -f deployment/cluster-autoscaler -n kube-system
```

## Production Considerations

### High Availability

#### Multi-Zone Deployment

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - bmasterai
      topologyKey: topology.kubernetes.io/zone
```

#### Load Balancing

```yaml
apiVersion: v1
kind: Service
metadata:
  name: bmasterai-service
  namespace: bmasterai
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: http
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: bmasterai
```

### Backup and Disaster Recovery

#### Persistent Volume Snapshots

```bash
# Create volume snapshot class
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: bmasterai-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Delete
EOF

# Create snapshot
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: bmasterai-snapshot
  namespace: bmasterai
spec:
  volumeSnapshotClassName: bmasterai-snapshot-class
  source:
    persistentVolumeClaimName: bmasterai-storage
EOF
```

#### Backup Strategy

```bash
# Use Velero for cluster backups
kubectl apply -f https://github.com/vmware-tanzu/velero/releases/latest/download/velero-v1.12.0-linux-amd64.tar.gz

# Create backup
velero backup create bmasterai-backup --include-namespaces bmasterai

# Schedule regular backups
velero schedule create bmasterai-daily --schedule="0 2 * * *" --include-namespaces bmasterai
```

### Security Hardening

#### Pod Security Context

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  fsGroup: 1001
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
    - ALL
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
```

#### Image Security

```bash
# Sign images with cosign
cosign sign bmasterai:v1.2.0

# Verify image signatures
cosign verify bmasterai:v1.2.0
```

### Compliance

#### CIS Benchmark

Run CIS Kubernetes Benchmark:
```bash
# Install kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# View results
kubectl logs job/kube-bench
```

#### Policy as Code

Use OPA Gatekeeper for policy enforcement:
```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: requireresourcelimits
spec:
  crd:
    spec:
      names:
        kind: RequireResourceLimits
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package requireresourcelimits
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.cpu
          msg := "Container must have CPU limits"
        }
```

### Cost Optimization

#### Resource Right-Sizing

Use VPA recommendations:
```bash
kubectl describe vpa bmasterai-vpa -n bmasterai
```

#### Spot Instances

Configure node groups with spot instances:
```yaml
# EKS managed node group with spot
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: bmasterai-cluster
  region: us-west-2

managedNodeGroups:
- name: spot-workers
  instanceTypes:
  - m5.large
  - m5.xlarge
  spot: true
  minSize: 1
  maxSize: 10
  desiredCapacity: 3
```

#### Resource Monitoring

Track costs with Kubecost:
```bash
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --create-namespace
```

### Updates and Maintenance

#### Rolling Updates

Configure deployment strategy:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 25%
    maxSurge: 25%
```

#### Automated Updates

Use ArgoCD for GitOps:
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

This comprehensive guide provides everything needed to successfully deploy and operate BMasterAI on Kubernetes in production environments. For specific questions or issues, refer to the troubleshooting section or open an issue in the GitHub repository.
