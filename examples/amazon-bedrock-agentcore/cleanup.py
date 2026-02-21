"""
Cleanup — tear down all AgentCore resources created by deploy.py.

Usage:
    uv run python cleanup.py
    uv run python cleanup.py --keep-memory   # retain Memory for future deploys
"""

import argparse
import logging
from pathlib import Path

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PARAM_MEMORY_ARN = "/bmasterai/agentcore/memory-arn"


def cleanup(region: str, role_name: str, keep_memory: bool = False) -> None:
    arn_file = Path(".agent_arn")
    ssm = boto3.client("ssm", region_name=region)
    iam = boto3.client("iam", region_name=region)

    # 1. Delete AgentCore Runtime
    if arn_file.exists():
        runtime_arn = arn_file.read_text().strip()
        logger.info(f"🗑️  Deleting AgentCore Runtime: {runtime_arn}")
        try:
            from bedrock_agentcore_starter_toolkit import Runtime
            runtime = Runtime()
            runtime.delete(runtime_arn)
            arn_file.unlink()
            logger.info("✅ Runtime deleted")
        except Exception as e:
            logger.error(f"❌ Failed to delete runtime: {e}")
    else:
        logger.info("ℹ️  No .agent_arn file found — skipping runtime deletion")

    # 2. Delete AgentCore Memory
    if not keep_memory:
        try:
            memory_arn = ssm.get_parameter(Name=PARAM_MEMORY_ARN)["Parameter"]["Value"]
            logger.info(f"🗑️  Deleting AgentCore Memory: {memory_arn}")
            from bedrock_agentcore.memory import MemoryClient
            client = MemoryClient(region_name=region)
            memory_id = memory_arn.split("/")[-1]
            client.delete_memory(memory_id)
            ssm.delete_parameter(Name=PARAM_MEMORY_ARN)
            logger.info("✅ Memory deleted")
        except ssm.exceptions.ParameterNotFound:
            logger.info("ℹ️  No memory ARN in SSM — skipping")
        except ImportError:
            logger.warning("⚠️  bedrock-agentcore not installed — cannot delete memory")
        except Exception as e:
            logger.error(f"❌ Memory deletion failed: {e}")
    else:
        logger.info("ℹ️  --keep-memory set — retaining AgentCore Memory")

    # 3. Delete IAM role inline policy
    try:
        iam.delete_role_policy(RoleName=role_name, PolicyName="BMasterAIAgentCorePolicy")
        iam.delete_role(RoleName=role_name)
        logger.info(f"✅ IAM role {role_name} deleted")
    except iam.exceptions.NoSuchEntityException:
        logger.info(f"ℹ️  IAM role {role_name} not found — skipping")
    except Exception as e:
        logger.error(f"❌ IAM role deletion failed: {e}")

    logger.info("\n✅ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(description="Tear down BMasterAI AgentCore resources")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--role-name", default="BMasterAIAgentCoreRole")
    parser.add_argument("--keep-memory", action="store_true", help="Retain AgentCore Memory")
    args = parser.parse_args()

    confirm = input("⚠️  This will delete all AgentCore resources. Continue? [y/N] ")
    if confirm.lower() != "y":
        print("Aborted.")
        return

    cleanup(region=args.region, role_name=args.role_name, keep_memory=args.keep_memory)


if __name__ == "__main__":
    main()
