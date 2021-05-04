# Court Reserve Bot
This project uses [Scrapy](https://docs.scrapy.org/en/latest/index.html) to make tennis court reservations.
## Getting started

- An AWS Secrets Manager secret is required for application configuration

- Run locally
```sh
DRY_RUN=true make local-invoke
```

## Deployment
AWS resources are defined and deployed using [AWS Cloud Development Kit (CDK)](https://docs.aws.amazon.com/cdk/latest/guide/cli.html)

- Helpful commands
```sh
# Synthesizes CloudFormation template
make synth

# Compares the deployed stack with the synthesized template
cdk diff

# Deploys CloudFormation stack
cdk deploy
```
