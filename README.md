# Court Reserve Bot
This project uses [Scrapy](https://docs.scrapy.org/en/latest/index.html) to make tennis court reservations.
## Getting started

- An AWS Secrets Manager secret is required for application configuration

- Run locally
```sh
DRY_RUN=true make local-invoke
```

## Deployment
AWS resource deployment is automated on merge to the main branch. This is the preferred method of deployment.
