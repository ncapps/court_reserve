""" court_reserve_stack
"""
from aws_cdk.core import Stack, Construct, Duration, BundlingOptions
from aws_cdk import (
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
)
from dotenv import dotenv_values

CONFIG = {**dotenv_values(".env")}


class CourtReserveStack(Stack):
    """Reserves court time on app.courtreserve.com"""

    def __init__(self, scope: Construct, construct_id, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_lambda/Function.html
        lambda_fn = lambda_.Function(
            self,
            "Function",
            description="Reserves a tennis court",
            code=lambda_.Code.from_asset(
                path="court_scheduler/court_reserve_lambda",
                bundling=BundlingOptions(
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
            timeout=Duration.seconds(30),
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
