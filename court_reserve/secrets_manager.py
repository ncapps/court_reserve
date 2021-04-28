#!/usr/bin/env python
""" Secrets Manager client
"""
import argparse
import base64
import boto3
from botocore.exceptions import ClientError


def get_secret(secret_name):
    """Returns Secrets Manager secret

    Args:
        secret_name (str): Name of the secret

    Returns:
        (str) Secret string

    Throws:
        (ClientError)
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as err:
        if err.response["Error"]["Code"] == "DecryptionFailureException":
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise err
        if err.response["Error"]["Code"] == "InternalServiceErrorException":
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise err
        if err.response["Error"]["Code"] == "InvalidParameterException":
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise err
        if err.response["Error"]["Code"] == "InvalidRequestException":
            # You provided a parameter value that is not valid for the current state
            # of the resource. Deal with the exception here, and/or rethrow at your discretion.
            raise err
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise err
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these
        # fields will be populated.
        if "SecretString" in get_secret_value_response:
            return get_secret_value_response["SecretString"]

        return base64.b64decode(get_secret_value_response["SecretBinary"])


def main():
    """command line interface"""

    parser = argparse.ArgumentParser(description="Secrets Manager client")

    parser.add_argument(
        "command",
        choices=["get-secret-value"],
        action="store",
        help="Indicates the action to be taken",
    )
    parser.add_argument("-n", "--name", action="store", help="Secret name")

    args = parser.parse_args()

    if args.command == "get-secret-value":
        secret = get_secret(args.name)
        print(secret)


if __name__ == "__main__":
    main()
