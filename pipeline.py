""" Pipeline stack
"""
from aws_cdk.core import Stack, Construct, SecretValue
from aws_cdk.pipelines import CdkPipeline, SimpleSynthAction
from aws_cdk.aws_codebuild import BuildEnvironment, LinuxBuildImage
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions


class CourtSchedulerPipelineStack(Stack):
    """Pipeline stack"""

    def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()

        environment = BuildEnvironment(
            build_image=LinuxBuildImage.STANDARD_5_0, privileged=True
        )

        CdkPipeline(
            self,
            "Pipeline",
            cloud_assembly_artifact=cloud_assembly_artifact,
            source_action=codepipeline_actions.GitHubSourceAction(
                action_name="GitHub",
                output=source_artifact,
                oauth_token=SecretValue.secrets_manager(
                    "github-token", json_field="oauthToken"
                ),
                trigger=codepipeline_actions.GitHubTrigger.POLL,
                owner="ncapps",
                repo="court_reserve",
                branch="feature/pipeline",
            ),
            synth_action=SimpleSynthAction(
                # Wait for docker to start
                install_commands=[
                    "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &",
                    'timeout 15 sh -c "until docker info; do echo .; sleep 1; done"',
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                ],
                synth_command="make build",
                source_artifact=source_artifact,
                cloud_assembly_artifact=cloud_assembly_artifact,
                environment=environment,
            ),
            cross_account_keys=False,
        )
