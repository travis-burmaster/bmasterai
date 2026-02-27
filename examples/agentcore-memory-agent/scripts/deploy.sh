#!/bin/bash
# ==========================================================================
# Deploy the AgentCore Memory Agent
# ==========================================================================
# End-to-end deployment script:
#   1. Create memory store
#   2. Deploy agent to AgentCore Runtime
#   3. Verify the deployment
#
# Prerequisites:
#   - pip install bedrock-agentcore-starter-toolkit
#   - AWS credentials configured
#   - Bot token already stored (run setup_telegram_webhook.sh first)
#
# Usage:
#   ./scripts/deploy.sh
# ==========================================================================

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"

echo "========================================="
echo " AgentCore Memory Agent — Deployment"
echo "========================================="
echo ""

# --------------------------------------------------------------------------
# Step 1: Create memory store (idempotent)
# --------------------------------------------------------------------------
echo "[Step 1] Setting up memory store..."
MEMORY_ID=$(python scripts/setup_memory.py 2>/dev/null | grep "Memory ID:" | awk '{print $NF}')

if [ -z "$MEMORY_ID" ]; then
    echo "  Failed to create/find memory store. Run manually:"
    echo "    python scripts/setup_memory.py"
    exit 1
fi

export MEMORY_ID
echo "  Memory ID: ${MEMORY_ID}"
echo ""

# --------------------------------------------------------------------------
# Step 2: Test locally (optional)
# --------------------------------------------------------------------------
echo "[Step 2] Local test (optional)..."
echo "  To test locally, open two terminals:"
echo "    Terminal 1:  agentcore dev"
echo "    Terminal 2:  agentcore invoke --dev '{\"actor_id\": \"tg_test\", \"prompt\": \"Hello!\"}'"
echo ""
read -p "  Press Enter to skip local testing and deploy, or Ctrl+C to stop... "

# --------------------------------------------------------------------------
# Step 3: Deploy to AgentCore Runtime
# --------------------------------------------------------------------------
echo ""
echo "[Step 3] Deploying to AgentCore Runtime..."
agentcore deploy

echo ""
echo "[Step 4] Verifying deployment..."
agentcore invoke '{"actor_id": "tg_test", "session_id": "deploy_test", "prompt": "Say hello and confirm you have memory, bash, browser, and telegram tools."}'

echo ""
echo "========================================="
echo " Deployment complete!"
echo "========================================="
echo ""
echo " Next steps:"
echo "   1. Note your Agent ID from the deploy output above"
echo "   2. Run the Telegram webhook setup:"
echo "      ./scripts/setup_telegram_webhook.sh <BOT_TOKEN>"
echo "   3. Deploy the webhook Lambda behind API Gateway"
echo "   4. Register the webhook URL with Telegram"
echo "   5. Send /start to your bot!"
echo ""
