"""court_scheduler_stage
"""
from aws_cdk.core import Construct, Stage

from court_scheduler.court_reserve_stack import CourtReserveStack


class CourtScheduler(Stage):
    """CourtScheduler application"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        CourtReserveStack(self, "CourtReserve")
