"""Deploy a DockerHub image to a new AWS EC2 instance."""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .config import (
    ALLOWED_DEPLOY_PORTS,
    ALLOWED_EC2_INSTANCE_TYPES,
    DEFAULT_AWS_REGION,
    DEFAULT_EC2_INSTANCE_TYPE,
)
from .settings import (
    default_aws_region,
    default_instance_type,
    default_security_group,
    dockerhub_credentials,
)


class DeploymentError(Exception):
    """Raised when a guarded deployment step cannot continue."""


@dataclass(frozen=True)
class DeployConfig:
    app_name: str
    dockerhub_repo: str
    tag: str
    host_port: int
    container_port: int
    region: str = DEFAULT_AWS_REGION
    instance_type: str = DEFAULT_EC2_INSTANCE_TYPE
    health_path: str = "/"


def _require_boto3():
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise DeploymentError("boto3 is required for EC2 deployment. Install with: pip install forge-engine") from exc
    return boto3, BotoCoreError, ClientError


def _validate_name(value: str, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{1,62}", value):
        raise DeploymentError(f"Invalid {field}: {value!r}")
    return value


def _validate_repo(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,}/[a-z0-9][a-z0-9_.-]{1,127}", value):
        raise DeploymentError("dockerhub_repo must look like 'username/repository' using lowercase Docker Hub names")
    return value


def _validate_tag(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,128}", value):
        raise DeploymentError(f"Invalid Docker image tag: {value!r}")
    return value


def _validate_port(value: int, field: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise DeploymentError(f"{field} must be an integer") from exc
    if port not in ALLOWED_DEPLOY_PORTS:
        allowed = ", ".join(str(port) for port in sorted(ALLOWED_DEPLOY_PORTS))
        raise DeploymentError(f"{field} must be one of: {allowed}")
    return port


def _validate_config(args: dict) -> DeployConfig:
    instance_type = args.get("instance_type") or default_instance_type()
    if instance_type not in ALLOWED_EC2_INSTANCE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_EC2_INSTANCE_TYPES))
        raise DeploymentError(f"instance_type must be one of: {allowed}")

    region = args.get("region") or default_aws_region() or DEFAULT_AWS_REGION
    if not re.fullmatch(r"[a-z]{2}-[a-z]+-\d", region):
        raise DeploymentError(f"Invalid AWS region: {region!r}")

    return DeployConfig(
        app_name=_validate_name(args["app_name"], "app_name"),
        dockerhub_repo=_validate_repo(args["dockerhub_repo"]),
        tag=_validate_tag(args.get("tag", "latest")),
        host_port=_validate_port(args["host_port"], "host_port"),
        container_port=_validate_port(args["container_port"], "container_port"),
        region=region,
        instance_type=instance_type,
        health_path=args.get("health_path", "/") or "/",
    )


def _run(command: list[str], cwd: Path | None = None, input_text: str | None = None, timeout: int = 900) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        output = (completed.stderr or completed.stdout).strip()
        raise DeploymentError(f"Command failed: {' '.join(command)}\n{output}")


def _latest_ubuntu_ami(ec2) -> str:
    images = ec2.describe_images(
        Owners=["099720109477"],
        Filters=[
            {"Name": "name", "Values": ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]},
            {"Name": "state", "Values": ["available"]},
            {"Name": "architecture", "Values": ["x86_64"]},
            {"Name": "virtualization-type", "Values": ["hvm"]},
        ],
    )["Images"]
    if not images:
        raise DeploymentError("Could not find an Ubuntu 22.04 AMI for this region")
    return sorted(images, key=lambda image: image["CreationDate"], reverse=True)[0]["ImageId"]


def _default_vpc_id(ec2) -> str:
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
    if not vpcs:
        raise DeploymentError("No default VPC found in this AWS region")
    return vpcs[0]["VpcId"]


def _ensure_security_group(ec2, app_port: int) -> str:
    group_name = default_security_group()
    vpc_id = _default_vpc_id(ec2)
    groups = ec2.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": [group_name]},
            {"Name": "vpc-id", "Values": [vpc_id]},
        ]
    )["SecurityGroups"]
    if groups:
        group_id = groups[0]["GroupId"]
    else:
        group_id = ec2.create_security_group(
            GroupName=group_name,
            Description="FORGE Engine Docker deployment access",
            VpcId=vpc_id,
        )["GroupId"]

    for port in {app_port}:
        try:
            ec2.authorize_security_group_ingress(
                GroupId=group_id,
                IpPermissions=[
                    {
                        "IpProtocol": "tcp",
                        "FromPort": port,
                        "ToPort": port,
                        "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "FORGE app port"}],
                    }
                ],
            )
        except Exception as exc:
            if "InvalidPermission.Duplicate" not in str(exc):
                raise
    return group_id


def _user_data(image: str, host_port: int, container_port: int) -> str:
    return f"""#!/bin/bash
set -euxo pipefail
apt-get update -y
apt-get install -y docker.io
systemctl enable --now docker
docker pull {image}
docker rm -f forge-app || true
docker run -d --restart unless-stopped --name forge-app -p {host_port}:{container_port} {image}
"""


def _docker_login(username: str, token: str) -> None:
    _run(["docker", "login", "-u", username, "--password-stdin"], input_text=token, timeout=120)


def deploy_dockerhub_to_ec2(sandbox_root: Path, args: dict) -> dict:
    """Build/push a Docker image, launch EC2, and run the image with user-data."""
    config = _validate_config(args)
    dockerfile = sandbox_root / "Dockerfile"
    if not dockerfile.is_file():
        raise DeploymentError("Dockerfile is missing. Create a Dockerfile before calling deploy_dockerhub_to_ec2.")

    username, token = dockerhub_credentials()
    if not username or not token:
        raise DeploymentError("Docker Hub credentials are not configured. Run: forge configure")
    if not config.dockerhub_repo.startswith(f"{username.lower()}/"):
        raise DeploymentError("dockerhub_repo must be under the authenticated Docker Hub username")

    local_image = f"forge-{config.app_name}:{config.tag}"
    remote_image = f"{config.dockerhub_repo}:{config.tag}"
    _run(["docker", "build", "-t", local_image, "."], cwd=sandbox_root)
    _run(["docker", "tag", local_image, remote_image])
    _docker_login(username, token)
    _run(["docker", "push", remote_image])

    boto3, BotoCoreError, ClientError = _require_boto3()
    try:
        ec2 = boto3.client("ec2", region_name=config.region)
        ami_id = _latest_ubuntu_ami(ec2)
        group_id = _ensure_security_group(ec2, config.host_port)
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=config.instance_type,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[group_id],
            UserData=_user_data(remote_image, config.host_port, config.container_port),
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": f"forge-{config.app_name}"},
                        {"Key": "forge-engine", "Value": "true"},
                    ],
                }
            ],
        )
        instance_id = response["Instances"][0]["InstanceId"]
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])
        description = ec2.describe_instances(InstanceIds=[instance_id])
        instance = description["Reservations"][0]["Instances"][0]
    except (BotoCoreError, ClientError) as exc:
        raise DeploymentError(f"AWS deployment failed: {exc}") from exc

    public_ip = instance.get("PublicIpAddress")
    if not public_ip:
        raise DeploymentError(f"EC2 instance {instance_id} is running but has no public IP")

    # Give cloud-init a short head start; the app may need more time after this.
    time.sleep(5)
    path = config.health_path if config.health_path.startswith("/") else f"/{config.health_path}"
    url = f"http://{public_ip}:{config.host_port}{path}"
    return {
        "status": "deployed",
        "image": remote_image,
        "instance_id": instance_id,
        "public_ip": public_ip,
        "url": url,
        "terminate_command": f"aws ec2 terminate-instances --instance-ids {instance_id} --region {config.region}",
    }


def deploy_dockerhub_to_ec2_json(sandbox_root: Path, args: dict) -> str:
    return json.dumps(deploy_dockerhub_to_ec2(sandbox_root, args), indent=2)
