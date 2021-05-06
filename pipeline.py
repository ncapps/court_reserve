""" Pipeline stack
"""
from aws_cdk.core import Stack, StackProps, Construct, SecretValue
from aws_cdk.pipelines import CdkPipeline, SimpleSynthAction

import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions


class CourtSchedulerPipelineStack(Stack):
    """Pipeline stack"""

    def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()

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
                install_commands=["npm install -g aws-cdk"],
                synth_command="make build",
                source_artifact=source_artifact,
                cloud_assembly_artifact=cloud_assembly_artifact,
            ),
        )
