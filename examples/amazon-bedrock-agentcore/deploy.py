"""
BMasterAI AgentCore Deployment Script
======================================
Automates:
  1. IAM execution role creation with required permissions
  2. AgentCore Memory provisioning (stored in SSM Parameter Store)
  3. Container build, ECR push, and AgentCore Runtime launch
     via bedrock-agentcore-starter-toolkit

Usage:
    uv run python deploy.py
    uv run python deploy.py --agent-name my-agent --region us-east-1
"""

import argparse
import json
import logging
import time
import uuid
from pathlib import Path

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AgentCoreDeployer:
    """Deploys the BMasterAI Research Agent to Amazon Bedrock AgentCore Runtime."""

    PARAM_MEMORY_ARN = "/bmasterai/agentcore/memory-arn"

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.account_id = boto3.client("sts", region_name=region).get_caller_identity()["Account"]
        self.iam = boto3.client("iam", region_name=region)
        self.ssm = boto3.client("ssm", region_name=region)

    # ── IAM ──────────────────────────────────────────────────────────────────

    def _execution_policy(self) -> dict:
        acct = self.account_id
        region = self.region
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockModelInvocation",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                    ],
                    "Resource": [
                        "arn:aws:bedrock:*::foundation-model/*",
                        f"arn:aws:bedrock:{region}:{acct}:*",
                    ],
                },
                {
                    "Sid": "BedrockKnowledgeBase",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve",
                        "bedrock:RetrieveAndGenerate",
                    ],
                    "Resource": f"arn:aws:bedrock:{region}:{acct}:knowledge-base/*",
                },
                {
                    "Sid": "AgentCoreMemory",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:ListMemories",
                        "bedrock-agentcore:ListEvents",
                        "bedrock-agentcore:CreateEvent",
                        "bedrock-agentcore:RetrieveMemories",
                        "bedrock-agentcore:GetMemoryStrategies",
                        "bedrock-agentcore:DeleteMemory",
                        "bedrock-agentcore:GetMemory",
                    ],
                    "Resource": f"arn:aws:bedrock-agentcore:{region}:{acct}:memory/*",
                },
                {
                    "Sid": "ECRAccess",
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "CloudWatchLogs",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                    ],
                    "Resource": [
                        f"arn:aws:logs:{region}:{acct}:log-group:/aws/bedrock-agentcore/runtimes/*",
                        f"arn:aws:logs:{region}:{acct}:log-group:*",
                    ],
                },
                {
                    "Sid": "XRayTracing",
                    "Effect": "Allow",
                    "Action": [
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords",
                        "xray:GetSamplingRules",
                        "xray:GetSamplingTargets",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "SSMParameters",
                    "Effect": "Allow",
                    "Action": ["ssm:GetParameter", "ssm:PutParameter"],
                    "Resource": f"arn:aws:ssm:{region}:{acct}:parameter/bmasterai/*",
                },
            ],
        }

    def create_execution_role(self, role_name: str) -> str:
        """Create (or update) the AgentCore execution IAM role."""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        try:
            logger.info(f"🔐 Creating IAM role: {role_name}")
            resp = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Execution role for BMasterAI Research Agent on AgentCore",
                Tags=[{"Key": "Project", "Value": "bmasterai-agentcore"}],
            )
            role_arn = resp["Role"]["Arn"]
            logger.info("⏳ Waiting for role propagation...")
            time.sleep(10)

        except self.iam.exceptions.EntityAlreadyExistsException:
            logger.info(f"📋 Role {role_name} already exists — updating policy")
            role_arn = self.iam.get_role(RoleName=role_name)["Role"]["Arn"]

        self.iam.put_role_policy(
            RoleName=role_name,
            PolicyName="BMasterAIAgentCorePolicy",
            PolicyDocument=json.dumps(self._execution_policy()),
        )
        logger.info(f"✅ IAM role ready: {role_arn}")
        return role_arn

    # ── AgentCore Memory ──────────────────────────────────────────────────────

    def provision_memory(self) -> str:
        """Create AgentCore Memory and persist the ARN in SSM."""
        # Return existing if already provisioned
        try:
            existing_arn = self.ssm.get_parameter(Name=self.PARAM_MEMORY_ARN)["Parameter"]["Value"]
            logger.info(f"✅ Using existing memory: {existing_arn}")
            return existing_arn
        except self.ssm.exceptions.ParameterNotFound:
            pass

        try:
            from bedrock_agentcore.memory import MemoryClient
            from bedrock_agentcore.memory.constants import StrategyType

            client = MemoryClient(region_name=self.region)
            suffix = uuid.uuid4().hex[:8]
            name = f"BMasterAIResearchAgent_{suffix}"

            logger.info(f"🧠 Creating AgentCore Memory: {name}")
            memory = client.create_memory_and_wait(
                name=name,
                description="Persistent memory for BMasterAI Research Agent — stores session context and user preferences",
                strategies=[
                    {
                        StrategyType.SEMANTIC.value: {
                            "name": "ResearchContext",
                            "description": "Retains research topics, findings, and analytical patterns across sessions",
                            "namespaces": ["bmasterai/research/{actorId}"],
                        }
                    },
                    {
                        StrategyType.USER_PREFERENCE.value: {
                            "name": "UserPreferences",
                            "description": "Remembers user preferences for output format, depth, and domain focus",
                            "namespaces": ["bmasterai/preferences/{actorId}"],
                        }
                    },
                ],
                event_expiry_days=90,
                max_wait=300,
                poll_interval=10,
            )

            memory_arn = memory["arn"]
            logger.info(f"✅ Memory created: {memory_arn}")

            self.ssm.put_parameter(
                Name=self.PARAM_MEMORY_ARN,
                Value=memory_arn,
                Type="String",
                Description="AgentCore Memory ARN for BMasterAI Research Agent",
                Tags=[{"Key": "Project", "Value": "bmasterai-agentcore"}],
            )
            logger.info("💾 Memory ARN saved to SSM Parameter Store")
            return memory_arn

        except ImportError:
            logger.warning("⚠️  bedrock-agentcore not installed — skipping memory provisioning")
            return ""

    # ── Deploy ────────────────────────────────────────────────────────────────

    def deploy(self, agent_name: str, role_name: str) -> str | None:
        """Full deploy: IAM → Memory → Container build → AgentCore launch."""
        logger.info("🚀 BMasterAI AgentCore Deployment")
        logger.info(f"   Agent: {agent_name} | Region: {self.region}")

        # 1. Provision memory
        memory_arn = self.provision_memory()

        # 2. Create execution role
        role_arn = self.create_execution_role(role_name)

        # 3. Deploy via starter toolkit
        try:
            from bedrock_agentcore_starter_toolkit import Runtime

            runtime = Runtime()
            runtime.configure(
                execution_role=role_arn,
                entrypoint="agent.py",
                requirements_file="pyproject.toml",
                region=self.region,
                agent_name=agent_name,
                auto_create_ecr=True,
                environment_variables={
                    "MEMORY_ARN": memory_arn,
                },
            )

            logger.info("📦 Building container and pushing to ECR...")
            runtime.launch(auto_update_on_conflict=True)

            status = runtime.status()
            runtime_arn = getattr(status, "agent_arn", None) or getattr(
                getattr(status, "config", None), "agent_arn", None
            )

            if runtime_arn:
                Path(".agent_arn").write_text(runtime_arn)
                agent_id = runtime_arn.split("/")[-1]
                log_group = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"

                logger.info("\n🎉 Deployment complete!")
                logger.info(f"   Runtime ARN : {runtime_arn}")
                logger.info(f"   Memory ARN  : {memory_arn}")
                logger.info(f"   Role ARN    : {role_arn}")
                logger.info(f"   CloudWatch  : {log_group}")
                logger.info(f"\n   Tail logs   : aws logs tail {log_group} --follow")
                logger.info("   Test locally: uv run python test_local.py")
                return runtime_arn
            else:
                logger.error("❌ Could not extract runtime ARN")
                return None

        except ImportError:
            logger.error("❌ bedrock-agentcore-starter-toolkit not installed")
            logger.info("   Install with: uv add bedrock-agentcore-starter-toolkit")
            return None
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            raise


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deploy BMasterAI Research Agent to Amazon Bedrock AgentCore"
    )
    parser.add_argument("--agent-name", default="bmasterai-research-agent")
    parser.add_argument("--role-name", default="BMasterAIAgentCoreRole")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    deployer = AgentCoreDeployer(region=args.region)
    result = deployer.deploy(agent_name=args.agent_name, role_name=args.role_name)

    if result:
        logger.info("\n✅ Ready. Run: uv run python test_local.py")
    else:
        logger.error("❌ Deployment failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
