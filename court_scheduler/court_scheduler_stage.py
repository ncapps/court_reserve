"""court_scheduler_stage
"""
from aws_cdk.core import Construct, Stage

from court_scheduler.court_scheduler_stack import CourtSchedulerStack


class CourtScheduler(Stage):
    """Tennis court scheduling application"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        CourtSchedulerStack(self, "CourtScheduler")
