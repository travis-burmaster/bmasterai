# BMasterAI Kubernetes Deployment

🚀 **Deploy BMasterAI on Amazon EKS with enterprise-grade features**

This repository now includes comprehensive Kubernetes deployment support for AWS EKS, making it easy to deploy and scale BMasterAI in production environments.

## ✨ What's New

### 🐳 Containerization
- **Production-ready Dockerfile** with security best practices
- **Multi-stage builds** for optimized image size
- **Non-root user** execution for enhanced security
- **Health checks** and proper signal handling

### ⚓ Kubernetes Native
- **Complete Kubernetes manifests** for EKS deployment
- **Helm chart** for easy installation and management
- **Auto-scaling** with Horizontal Pod Autoscaler
- **Persistent storage** for data and logs
- **ConfigMaps and Secrets** management

### 🛡️ Enterprise Security
- **RBAC** configuration with minimal permissions
- **Pod Security Standards** compliance
- **Network Policies** for traffic isolation
- **IAM Roles for Service Accounts** (IRSA) integration
- **Secrets management** with Kubernetes secrets

### 📊 Monitoring & Observability
- **Prometheus metrics** exposition
- **Grafana dashboards** for visualization
- **CloudWatch integration** for AWS logging
- **Service monitors** for automated scraping
- **Custom metrics** for BMasterAI-specific monitoring

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured
- eksctl installed
- kubectl installed
- Helm 3.x installed
- Docker (for building images)

### 1. Automated Deployment

```bash
# Clone the repository
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai

# Create EKS cluster
./eks/setup-scripts/01-create-cluster.sh

# Deploy BMasterAI
./eks/setup-scripts/02-deploy-bmasterai.sh

# Install monitoring (optional)
./eks/setup-scripts/03-install-monitoring.sh
```

### 2. Using Helm (Recommended)

```bash
# Create namespace
kubectl create namespace bmasterai

# Install with Helm
helm install bmasterai ./helm/bmasterai \
  --namespace bmasterai \
  --set secrets.openaiApiKey=$(echo -n "your-api-key" | base64)
```

### 3. Using kubectl

```bash
# Apply all manifests
kubectl apply -f k8s/
```

## 📁 Repository Structure

```
bmasterai/
├── Dockerfile                    # Container image definition
├── k8s/                         # Kubernetes manifests
│   ├── namespace.yaml           # Namespace and resource quotas
│   ├── configmap.yaml           # Application configuration
│   ├── secrets.yaml             # Secrets template
│   ├── service-account.yaml     # RBAC configuration
│   ├── persistent-volume.yaml   # Storage configuration
│   ├── deployment.yaml          # Main application deployment
│   ├── service.yaml             # Service definitions
│   ├── hpa.yaml                 # Horizontal Pod Autoscaler
│   └── monitoring.yaml          # Monitoring configuration
├── helm/bmasterai/              # Helm chart
│   ├── Chart.yaml               # Chart metadata
│   ├── values.yaml              # Default configuration
│   └── templates/               # Kubernetes templates
├── eks/                         # EKS-specific configuration
│   ├── cluster-config.yaml      # eksctl cluster configuration
│   ├── aws-iam-policy.json      # IAM policy for BMasterAI
│   └── setup-scripts/           # Automation scripts
└── docs/kubernetes-deployment.md # Detailed documentation
```

## 🔧 Configuration

### Required Secrets

Update `k8s/secrets.yaml` or create secrets directly:

```bash
kubectl create secret generic bmasterai-secrets \
  --from-literal=OPENAI_API_KEY=your-openai-key \
  --from-literal=ANTHROPIC_API_KEY=your-anthropic-key \
  --from-literal=SLACK_WEBHOOK_URL=your-slack-webhook \
  --namespace bmasterai
```

### Helm Configuration

Customize deployment with Helm values:

```yaml
# values-production.yaml
replicaCount: 5

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20

secrets:
  openaiApiKey: "eW91ci1hcGkta2V5"  # base64 encoded
```

## 📊 Monitoring

### Access Grafana Dashboard

```bash
# Port forward to Grafana
kubectl port-forward svc/prometheus-operator-grafana 3000:80 -n monitoring

# Open http://localhost:3000
# Username: admin
# Password: (get from secret)
kubectl get secret prometheus-operator-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 --decode
```

### View Metrics

```bash
# BMasterAI metrics endpoint
kubectl port-forward svc/bmasterai-service 8080:80 -n bmasterai
curl http://localhost:8080/metrics
```

## 🔍 Monitoring Commands

```bash
# Check deployment status
kubectl get pods -n bmasterai
kubectl get hpa -n bmasterai

# View logs
kubectl logs -f deployment/bmasterai-agent -n bmasterai

# Scale manually
kubectl scale deployment bmasterai-agent --replicas=5 -n bmasterai

# Port forward for direct access
kubectl port-forward svc/bmasterai-service 8080:80 -n bmasterai
```

## 🧹 Cleanup

```bash
# Remove application only
helm uninstall bmasterai -n bmasterai

# Remove everything including cluster
./eks/setup-scripts/04-cleanup.sh
```

## 🏗️ Architecture

### EKS Cluster
- **Region**: us-west-2 (configurable)
- **Node Groups**: m5.large instances with auto-scaling
- **Storage**: EBS GP3 volumes with encryption
- **Networking**: VPC with public/private subnets
- **Security**: IRSA, Pod Security Standards, Network Policies

### BMasterAI Deployment
- **Replicas**: 2 (auto-scaling 2-10 based on CPU/memory)
- **Resources**: 200m CPU, 256Mi RAM (expandable)
- **Storage**: Persistent volumes for data and logs
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **High Availability**: Pod anti-affinity, rolling updates

## 🔐 Security Features

### Container Security
- Non-root user execution (UID 1001)
- Read-only root filesystem where possible
- Minimal container image with security scanning
- Resource limits and security contexts

### Kubernetes Security
- RBAC with minimal required permissions
- Pod Security Standards enforcement
- Network policies for traffic isolation
- Secrets management with encryption at rest

### AWS Integration
- IAM Roles for Service Accounts (IRSA)
- VPC security groups and NACLs
- CloudTrail for audit logging
- GuardDuty for threat detection

## 📈 Scaling and Performance

### Horizontal Pod Autoscaler
```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Cluster Autoscaler
- Automatic node scaling based on pod demands
- Multi-AZ deployment for high availability
- Spot instances support for cost optimization

### Performance Monitoring
- Real-time metrics collection
- Custom BMasterAI metrics
- Performance dashboards
- Alerting on performance thresholds

## 💰 Cost Optimization

### Resource Efficiency
- Right-sized resource requests and limits
- Horizontal Pod Autoscaling for optimal utilization
- Cluster Autoscaler for dynamic node management

### AWS Cost Features
- Spot instances for development/testing
- Reserved instances for production workloads
- EBS GP3 volumes for cost-effective storage
- CloudWatch cost monitoring

## 🔄 CI/CD Integration

### Image Building
```bash
# Build and tag
docker build -t bmasterai:${VERSION} .
docker tag bmasterai:${VERSION} ${ECR_REGISTRY}/bmasterai:${VERSION}

# Push to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
docker push ${ECR_REGISTRY}/bmasterai:${VERSION}
```

### Deployment Automation
```bash
# Helm upgrade
helm upgrade bmasterai ./helm/bmasterai \
  --set image.tag=${VERSION} \
  --namespace bmasterai

# Verify deployment
kubectl rollout status deployment/bmasterai-agent -n bmasterai
```

## 🆘 Troubleshooting

### Common Issues

1. **Pod startup failures**
```bash
kubectl describe pod <pod-name> -n bmasterai
kubectl logs <pod-name> -n bmasterai
```

2. **Resource constraints**
```bash
kubectl top nodes
kubectl top pods -n bmasterai
```

3. **Network connectivity**
```bash
kubectl exec -it <pod-name> -n bmasterai -- nslookup kubernetes.default
```

### Support Channels
- GitHub Issues: [bmasterai/issues](https://github.com/travis-burmaster/bmasterai/issues)
- Documentation: [kubernetes-deployment.md](docs/kubernetes-deployment.md)
- Community: GitHub Discussions

## 🎯 Roadmap

### Version 0.3.0
- [ ] **Advanced auto-scaling** with custom metrics
- [ ] **Multi-region deployment** support
- [ ] **Istio service mesh** integration
- [ ] **GitOps deployment** with ArgoCD

### Version 0.4.0
- [ ] **Serverless deployment** with Knative
- [ ] **GPU workload** optimization
- [ ] **Advanced monitoring** with distributed tracing
- [ ] **Backup and disaster recovery** automation

## 📚 Documentation

- **[Complete Deployment Guide](docs/kubernetes-deployment.md)** - Detailed step-by-step instructions
- **[Main README](README.md)** - BMasterAI framework overview
- **[Helm Chart Documentation](helm/bmasterai/README.md)** - Helm-specific configuration
- **[Security Guide](docs/security.md)** - Security best practices

## 🤝 Contributing

We welcome contributions to improve the Kubernetes deployment:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Areas for Contribution
- Additional cloud provider support (GKE, AKS)
- Enhanced monitoring and alerting
- Performance optimizations
- Security improvements
- Documentation updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to deploy BMasterAI on Kubernetes? 🚀**

Start with the [Quick Start](#-quick-start) section above, or dive into the [Complete Deployment Guide](docs/kubernetes-deployment.md) for detailed instructions.

**Questions or issues?** Open an issue on [GitHub](https://github.com/travis-burmaster/bmasterai/issues) or join our community discussions.

**Made with ❤️ for the BMasterAI community**