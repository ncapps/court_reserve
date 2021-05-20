# Tennis Court Scheduler
This application makes tennis court reservations based on court availability and configured preferences.

## Getting started

- An AWS Secrets Manager secret is used for storing court reservation application credentials and schedule preferences.
```json
{
    "ORG_ID": "<Organization Id>",
    "USERNAME": "<Username>",
    "PASSWORD": "<Password>",
    "PREFERENCES_V2": {
        "wednesday": {
            "start_end_times": [
                [
                    "12:00 PM",
                    "1:00 PM"
                ],
                [
                    "1:00 PM",
                    "2:00 PM"
                ]
            ],
            "courts": [
                "Court #1",
                "Court #3",
                "Court #5"
            ],
            "players": [
                "billie jean king"
            ]
        }
      }
   }
}
```

- Run in a lambda-like environment locally
```sh
make local-invoke
```

## Continuous Deployment
- This project builds and deploys on merge to the `main` branch using AWS CodePipeline
