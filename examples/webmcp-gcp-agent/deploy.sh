#!/bin/bash
# Deploy WebMCP GCP Agent to Cloud Run
# Usage: ./deploy.sh [project-id] [region] [--authenticated]
#
# Authentication:
#   By default, both services require IAM authentication (recommended for
#   production). Pass --allow-unauthenticated as the 3rd argument for open
#   demo deployments, or set WEBMCP_ALLOW_UNAUTHENTICATED=true in your env.
#
# Example (open/demo):
#   ./deploy.sh my-project us-central1 --allow-unauthenticated
#
# Example (production, authenticated):
#   ./deploy.sh my-project us-central1

set -e

PROJECT="${1:-$(gcloud config get-value project)}"
REGION="${2:-us-central1}"
AGENT_SERVICE="webmcp-agent"
SITE_SERVICE="webmcp-demo-site"

# Auth flag: default to IAM-authenticated (secure).
# Use --allow-unauthenticated for demos or behind a corporate load balancer.
AUTH_FLAG="--no-allow-unauthenticated"
if [[ "${3}" == "--allow-unauthenticated" ]] || [[ "${WEBMCP_ALLOW_UNAUTHENTICATED}" == "true" ]]; then
  AUTH_FLAG="--allow-unauthenticated"
  echo "⚠️  WARNING: Deploying WITHOUT authentication. Anyone with the URL can call these services."
  echo "   For production, use IAM authentication and invoke via Identity Token."
  echo ""
fi

echo "🚀 Deploying WebMCP GCP Agent"
echo "   Project: $PROJECT"
echo "   Region:  $REGION"
echo "   Auth:    $( [[ "$AUTH_FLAG" == "--allow-unauthenticated" ]] && echo 'open (unauthenticated)' || echo 'IAM required' )"
echo ""

# ── Deploy demo site ──────────────────────────────────────────────────────────
echo "📦 Deploying demo site..."
gcloud run deploy "$SITE_SERVICE" \
  --source ./demo-site \
  --region "$REGION" \
  --project "$PROJECT" \
  $AUTH_FLAG \
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
  $AUTH_FLAG \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 120 \
  --set-env-vars "DEMO_SITE_URL=$SITE_URL,GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_REGION=$REGION" \
  --quiet

AGENT_URL=$(gcloud run services describe "$AGENT_SERVICE" \
  --region "$REGION" --project "$PROJECT" \
  --format "value(status.url)")

echo "✅ Agent: $AGENT_URL"
echo ""

# ── Smoke test ────────────────────────────────────────────────────────────────
echo "🧪 Running smoke test..."

# Build auth header for curl (no-op when unauthenticated)
if [[ "$AUTH_FLAG" == "--no-allow-unauthenticated" ]]; then
  AUTH_HEADER="Authorization: Bearer $(gcloud auth print-identity-token)"
else
  AUTH_HEADER="X-No-Auth: true"
fi

echo "  GET $AGENT_URL/health"
curl -s -H "$AUTH_HEADER" "$AGENT_URL/health" | python3 -m json.tool

echo ""
echo "  GET $AGENT_URL/tools"
curl -s -H "$AUTH_HEADER" "$AGENT_URL/tools" | python3 -m json.tool

echo ""
echo "────────────────────────────────────────────"
echo "✅ Deployment complete!"
echo ""
echo "Try it:"
if [[ "$AUTH_FLAG" == "--no-allow-unauthenticated" ]]; then
echo "  # Add identity token for IAM-authenticated calls:"
echo "  TOKEN=\$(gcloud auth print-identity-token)"
echo "  curl -X POST $AGENT_URL/run \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H \"Authorization: Bearer \$TOKEN\" \\"
echo "    -d '{\"task\": \"Find me a laptop under \$1000 and add it to the cart\"}'"
else
echo "  curl -X POST $AGENT_URL/run \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"task\": \"Find me a laptop under \$1000 and add it to the cart\"}'"
fi
