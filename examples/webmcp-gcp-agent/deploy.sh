#!/bin/bash
# Deploy WebMCP GCP Agent to Cloud Run
# Usage: ./deploy.sh [project-id] [region]

set -e

PROJECT="${1:-$(gcloud config get-value project)}"
REGION="${2:-us-central1}"
AGENT_SERVICE="webmcp-agent"
SITE_SERVICE="webmcp-demo-site"

echo "🚀 Deploying WebMCP GCP Agent"
echo "   Project: $PROJECT"
echo "   Region:  $REGION"
echo ""

# ── Deploy demo site ──────────────────────────────────────────────────────────
echo "📦 Deploying demo site..."
gcloud run deploy "$SITE_SERVICE" \
  --source ./demo-site \
  --region "$REGION" \
  --project "$PROJECT" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 256Mi \
  --cpu 1 \
  --quiet

SITE_URL=$(gcloud run services describe "$SITE_SERVICE" \
  --region "$REGION" --project "$PROJECT" \
  --format "value(status.url)")

echo "✅ Demo site: $SITE_URL"
echo ""

# ── Deploy agent ──────────────────────────────────────────────────────────────
echo "🤖 Deploying agent..."
gcloud run deploy "$AGENT_SERVICE" \
  --source ./agent \
  --region "$REGION" \
  --project "$PROJECT" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "DEMO_SITE_URL=$SITE_URL,GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_REGION=$REGION" \
  --quiet

AGENT_URL=$(gcloud run services describe "$AGENT_SERVICE" \
  --region "$REGION" --project "$PROJECT" \
  --format "value(status.url)")

echo "✅ Agent: $AGENT_URL"
echo ""

# ── Smoke test ────────────────────────────────────────────────────────────────
echo "🧪 Running smoke test..."

echo "  GET $AGENT_URL/health"
curl -s "$AGENT_URL/health" | python3 -m json.tool

echo ""
echo "  GET $AGENT_URL/tools"
curl -s "$AGENT_URL/tools" | python3 -m json.tool

echo ""
echo "────────────────────────────────────────────"
echo "✅ Deployment complete!"
echo ""
echo "Try it:"
echo "  curl -X POST $AGENT_URL/run \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"task\": \"Find me a laptop under \$1000 and add it to the cart\"}'"
