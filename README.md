# Court Reserve Bot
This project uses [Scrapy](https://docs.scrapy.org/en/latest/index.html) to make tennis court reservations.
## Getting started

- An AWS Secrets Manager secret is required for application configuration

- Run locally
```sh
make run-local
```

## Deployment
AWS resources are defined and deployed using [AWS Cloud Development Kit (CDK)](https://docs.aws.amazon.com/cdk/latest/guide/cli.html)

- Helpful commands
```sh
# Synthesizes CloudFormation template
make synth

# Deploys CloudFormation stack
cdk deploy

# Compares the deployed stack with the synthesized template
cdk diff
```
