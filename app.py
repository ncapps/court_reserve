""" Build AWS cloud resources
"""
#!/usr/bin/env python3

import os
from pathlib import Path

from aws_cdk import (
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    core as cdk,
)
from dotenv import dotenv_values
from pipeline import CourtSchedulerPipelineStack

CONFIG = {**dotenv_values(".env")}


class LambdaStack(cdk.Stack):
    """Lambda cron to reserve court time"""

    def __init__(self, scope, id_, **kwargs):
        super().__init__(scope, id_, **kwargs)

        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_lambda/Function.html
        lambda_fn = lambda_.Function(
            self,
            "Function",
            description="Reserves a tennis court",
            code=lambda_.Code.from_asset(
                path=str(Path("court_reserve").resolve()),
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_8.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements_lock.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            environment={**CONFIG},
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="court_reserve.handler",
            memory_size=512,
            timeout=cdk.Duration.seconds(30),
            log_retention=logs.RetentionDays.TWO_WEEKS,
        )

        # Run every day at 9AM PDT (UTC -7)
        rule = events.Rule(
            self,
            "Rule",
            schedule=events.Schedule.cron(minute="0", hour="16"),
        )
        rule.add_target(targets.LambdaFunction(lambda_fn))

        # Grant read access to secret
        secret = secretsmanager.Secret.from_secret_name_v2(
            self, "SecretFromName", CONFIG["SECRET_ID"]
        )
        secret.grant_read(lambda_fn)

        self.export_value(lambda_fn.function_name, name="lambdaCronFunctionName")


app = cdk.App()
# https://docs.aws.amazon.com/cdk/latest/guide/environments.html
env = cdk.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]),
)

LambdaStack(app, "CourtSchedulerLambdaStack", env=env)
CourtSchedulerPipelineStack(app, "CourtSchedulerPipeline", env=env)
app.synth()
