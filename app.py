""" Build AWS cloud resources
"""
from pathlib import Path
import os

from aws_cdk import (
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    core as cdk,
)


class LambdaStack(cdk.Stack):
    """Lambda cron to reserve court time"""

    def __init__(self, app_, id_):
        super().__init__(app_, id_)

        lambda_fn = lambda_.Function(
            self,
            "Function",
            code=lambda_.Code.from_asset(
                path=str(Path("court_reserve").resolve()),
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_8.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="court_reserve.handler",
        )

        # Run every day at 9AM PDT (UTC -7)
        rule = events.Rule(
            self,
            "Rule",
            schedule=events.Schedule.cron(minute="0", hour="16"),
        )
        rule.add_target(targets.LambdaFunction(lambda_fn))


app = cdk.App()
LambdaStack(app, "LambdaStack")
app.synth()
