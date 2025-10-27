# Launch Agents on Kubernetes

*Need the full infrastructure breakdown? See [`README-k8s.content.md`](README-k8s.content.md).*

> Turn your winning demos into always-on experiences. This guide shows how to deploy BMasterAI on Amazon EKS so marketing, product, and ops teams stay in sync.

## Why Take It to the Cloud?
- **Campaign uptime:** Keep flagship agents live for trials, events, or customer pilots.
- **Scalable storytelling:** Auto-scale pods so surging traffic never cuts the narrative short.
- **Proof with telemetry:** Ship the same reasoning logs and cost metrics your launch team shares in recaps.

## Fast-Track Checklist
1. **Prep your runway** – Install AWS CLI, `eksctl`, `kubectl`, Helm 3, and Docker.
2. **Clone + configure** – `git clone https://github.com/travis-burmaster/bmasterai.git && cd bmasterai`.
3. **Create the stage** – Run `./eks/setup-scripts/01-create-cluster.sh` to spin up an EKS cluster tuned for demos.
4. **Deploy the stars** – Use `./eks/setup-scripts/02-deploy-bmasterai.sh` or `helm install bmasterai ./helm/bmasterai --namespace bmasterai`.
5. **Instrument the win** – Activate `./eks/setup-scripts/03-install-monitoring.sh` to surface Grafana dashboards for your recap deck.

## Helm Snippet (Recommended)
```bash
kubectl create namespace bmasterai
helm install bmasterai ./helm/bmasterai \
  --namespace bmasterai \
  --set secrets.openaiApiKey=$(echo -n "your-api-key" | base64)
```

## Secrets to Set
```bash
kubectl create secret generic bmasterai-secrets \
  --from-literal=OPENAI_API_KEY=your-openai-key \
  --from-literal=ANTHROPIC_API_KEY=your-anthropic-key \
  --from-literal=SLACK_WEBHOOK_URL=your-slack-webhook \
  --namespace bmasterai
```

## Monitor the Show
```bash
kubectl port-forward svc/prometheus-operator-grafana 3000:80 -n monitoring
open http://localhost:3000
kubectl get secret prometheus-operator-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 --decode
```

## Folder Map
```
k8s/                # Manifests for declarative launches
helm/bmasterai/     # Helm chart powering one-line installs
eks/setup-scripts/  # Automation for cluster + observability
```

Need more operations detail? Head to `docs/kubernetes-deployment.md` for production checklists, SLO ideas, and privacy notes you can share with security teams.