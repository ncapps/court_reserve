""" pipeline_stack
"""
from aws_cdk.core import Stack, Construct, SecretValue
from aws_cdk.pipelines import CdkPipeline, SimpleSynthAction
from aws_cdk.aws_codebuild import BuildEnvironment, LinuxBuildImage
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions

from court_scheduler.court_scheduler_stage import CourtScheduler


class PipelineStack(Stack):
    """PipelineStack"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()

        build_env = BuildEnvironment(
            build_image=LinuxBuildImage.STANDARD_5_0, privileged=True
        )

        pipeline = CdkPipeline(
            self,
            "Pipeline",
            cloud_assembly_artifact=cloud_assembly_artifact,
            source_action=codepipeline_actions.GitHubSourceAction(
                action_name="GitHub",
                output=source_artifact,
                oauth_token=SecretValue.secrets_manager(
                    "github-token", json_field="oauthToken"
                ),
                owner="ncapps",
                repo="court_reserve",
                # TODO set to main for continuous delivery
                branch="feature/pipeline",
            ),
            synth_action=SimpleSynthAction(
                # Wait for docker to start
                install_commands=[
                    "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &",
                    'timeout 15 sh -c "until docker info; do echo .; sleep 1; done"',
                    "npm install -g aws-cdk",
                    "python -m pip install --upgrade pip",
                    "pip install -r requirements.txt",
                ],
                synth_command="make build",
                source_artifact=source_artifact,
                cloud_assembly_artifact=cloud_assembly_artifact,
                environment=build_env,
            ),
            cross_account_keys=False,
        )

        pipeline.add_application_stage(CourtScheduler(self, "Prod", env=kwargs["env"]))
