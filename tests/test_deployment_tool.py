import json

import pytest

from harness import orchestrator
from harness.ec2_deployer import DeploymentError, deploy_dockerhub_to_ec2
from harness.sandbox import Sandbox
from harness.tools import TOOLS, dispatch_tool
from tests.fake_llm_client import FakeLLMClient, response, tool_call


def test_deploy_tool_is_registered():
    names = {tool["function"]["name"] for tool in TOOLS}

    assert "deploy_dockerhub_to_ec2" in names


def test_deploy_tool_is_blocked_without_deploy_intent(tmp_path):
    sandbox = Sandbox(tmp_path)

    result = dispatch_tool(
        sandbox,
        "deploy_dockerhub_to_ec2",
        {
            "app_name": "demo-app",
            "dockerhub_repo": "devakesavan/demo-app",
            "host_port": 3000,
            "container_port": 3000,
        },
        allow_deployment=False,
    )

    assert result.startswith("ERROR: deployment blocked")


def test_deploy_requires_dockerfile_before_credentials(tmp_path):
    with pytest.raises(DeploymentError, match="Dockerfile is missing"):
        deploy_dockerhub_to_ec2(
            tmp_path,
            {
                "app_name": "demo-app",
                "dockerhub_repo": "devakesavan/demo-app",
                "host_port": 3000,
                "container_port": 3000,
            },
        )


def test_orchestrator_blocks_deploy_tool_for_normal_tasks(tmp_path, monkeypatch):
    fake = FakeLLMClient(
        [
            response(
                tool_calls=[
                    tool_call(
                        "deploy_dockerhub_to_ec2",
                        json.dumps(
                            {
                                "app_name": "demo-app",
                                "dockerhub_repo": "devakesavan/demo-app",
                                "host_port": 3000,
                                "container_port": 3000,
                            }
                        ),
                    )
                ]
            ),
            response(content="No more tools."),
        ]
    )
    monkeypatch.setattr(orchestrator, "LocalLLMClient", lambda *args, **kwargs: fake)

    result = orchestrator.run("create a Dockerfile", str(tmp_path), None)

    assert result["status"] == "stalled"


def test_orchestrator_allows_deploy_tool_for_aws_deploy_tasks(tmp_path, monkeypatch):
    fake = FakeLLMClient(
        [
            response(
                tool_calls=[
                    tool_call(
                        "deploy_dockerhub_to_ec2",
                        json.dumps(
                            {
                                "app_name": "demo-app",
                                "dockerhub_repo": "devakesavan/demo-app",
                                "host_port": 3000,
                                "container_port": 3000,
                            }
                        ),
                    )
                ]
            ),
            response(content="No more tools."),
        ]
    )
    calls = []

    def fake_dispatch(sandbox, name, args, allow_deployment=False):
        calls.append((name, allow_deployment))
        return "deployed"

    monkeypatch.setattr(orchestrator, "LocalLLMClient", lambda *args, **kwargs: fake)
    monkeypatch.setattr(orchestrator, "dispatch_tool", fake_dispatch)

    result = orchestrator.run("deploy this app to AWS EC2", str(tmp_path), None)

    assert result["status"] == "stalled"
    assert calls == [("deploy_dockerhub_to_ec2", True)]
