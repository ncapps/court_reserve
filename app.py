""" Build AWS cloud resources
"""
from pathlib import Path

from aws_cdk import (
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    core as cdk,
)

SECRET_ID = "court_reserve_secret"


class LambdaStack(cdk.Stack):
    """Lambda cron to reserve court time"""

    def __init__(self, app_, id_):
        super().__init__(app_, id_)

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
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            environment={
                "SECRET_ID": SECRET_ID,
                "SECRET_FILE": "config.json",
                "ENVIRONMENT": "prod",
            },
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
            self, "SecretFromName", SECRET_ID
        )
        secret.grant_read(lambda_fn)


app = cdk.App()
LambdaStack(app, "LambdaStack")
app.synth()
