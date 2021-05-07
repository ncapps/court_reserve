""" CDK app
"""
#!/usr/bin/env python3

import os

from aws_cdk.core import App, Environment

from pipeline.pipeline_stack import PipelineStack


# https://docs.aws.amazon.com/cdk/latest/guide/environments.html
environment = Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]),
)

app = App()
PipelineStack(app, "CourtSchedulerPipeline", env=environment)
app.synth()
