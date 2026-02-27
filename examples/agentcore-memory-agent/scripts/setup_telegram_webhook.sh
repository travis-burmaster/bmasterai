#!/bin/bash
# ==========================================================================
# Setup Telegram Bot Webhook
# ==========================================================================
# This script:
#   1. Stores the bot token in AWS Secrets Manager
#   2. Creates a DynamoDB table for session tracking
#   3. Deploys the webhook Lambda + API Gateway
#   4. Registers the webhook URL with Telegram
#
# Prerequisites:
#   - AWS CLI configured with appropriate permissions
#   - A Telegram bot token from @BotFather
#
# Usage:
#   ./scripts/setup_telegram_webhook.sh <BOT_TOKEN> <AWS_REGION>
# ==========================================================================

set -euo pipefail

BOT_TOKEN="${1:?Usage: $0 <BOT_TOKEN> [AWS_REGION]}"
REGION="${2:-us-east-1}"
STACK_NAME="telegram-agent-webhook"
SECRET_NAME="telegram-bot-token"
SESSION_TABLE="telegram-agent-sessions"

echo "=== Telegram Agent Webhook Setup ==="
echo "Region: ${REGION}"
echo ""

# --------------------------------------------------------------------------
# 1. Store bot token in Secrets Manager
# --------------------------------------------------------------------------
echo "[1/4] Storing bot token in Secrets Manager..."

if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "  Secret already exists — updating..."
    aws secretsmanager put-secret-value \
        --secret-id "$SECRET_NAME" \
        --secret-string "{\"bot_token\": \"${BOT_TOKEN}\"}" \
        --region "$REGION"
else
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "Telegram bot token for the memory agent" \
        --secret-string "{\"bot_token\": \"${BOT_TOKEN}\"}" \
        --region "$REGION"
fi
echo "  Done."

# --------------------------------------------------------------------------
# 2. Create DynamoDB session table
# --------------------------------------------------------------------------
echo "[2/4] Creating DynamoDB session table..."

if aws dynamodb describe-table --table-name "$SESSION_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "  Table already exists — skipping."
else
    aws dynamodb create-table \
        --table-name "$SESSION_TABLE" \
        --attribute-definitions \
            AttributeName=chat_id,AttributeType=S \
        --key-schema \
            AttributeName=chat_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --tags Key=Project,Value=telegram-memory-agent

    # Enable TTL for automatic session cleanup
    aws dynamodb update-time-to-live \
        --table-name "$SESSION_TABLE" \
        --time-to-live-specification "Enabled=true, AttributeName=ttl" \
        --region "$REGION"

    echo "  Table created with TTL enabled."
fi

# --------------------------------------------------------------------------
# 3. Package and deploy webhook Lambda
# --------------------------------------------------------------------------
echo "[3/4] Packaging webhook Lambda..."

PACKAGE_DIR=$(mktemp -d)
cp webhook/handler.py "$PACKAGE_DIR/lambda_function.py"
cp -r memory "$PACKAGE_DIR/"
pip install requests -t "$PACKAGE_DIR" --quiet

cd "$PACKAGE_DIR"
zip -r9 /tmp/webhook-lambda.zip . >/dev/null
cd -

echo "  Packaged to /tmp/webhook-lambda.zip"
echo ""
echo "  Deploy with SAM, CDK, or manually:"
echo "    aws lambda create-function \\"
echo "      --function-name telegram-agent-webhook \\"
echo "      --runtime python3.12 \\"
echo "      --handler lambda_function.lambda_handler \\"
echo "      --zip-file fileb:///tmp/webhook-lambda.zip \\"
echo "      --role <LAMBDA_EXECUTION_ROLE_ARN> \\"
echo "      --environment Variables={AGENTCORE_AGENT_ID=<AGENT_ID>,MEMORY_ID=<MEMORY_ID>,SESSION_TABLE=${SESSION_TABLE},TELEGRAM_BOT_TOKEN_SECRET=${SECRET_NAME}} \\"
echo "      --timeout 120 \\"
echo "      --memory-size 256 \\"
echo "      --region ${REGION}"

# --------------------------------------------------------------------------
# 4. Register webhook with Telegram (once you have the API Gateway URL)
# --------------------------------------------------------------------------
echo ""
echo "[4/4] Registering Telegram webhook..."
echo ""
echo "  After deploying the Lambda behind API Gateway, run:"
echo ""
echo "    curl -X POST \"https://api.telegram.org/bot${BOT_TOKEN}/setWebhook\" \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"url\": \"https://<YOUR_API_GW_URL>/webhook\"}'"
echo ""
echo "  Verify with:"
echo "    curl \"https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo\""
echo ""
echo "=== Setup complete ==="
