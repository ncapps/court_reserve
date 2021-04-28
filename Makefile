.PHONY: get-secret update-secret

SECRET_ID = court_reserve_secret
SECRET_FILE = config.json

get-secret:
	aws secretsmanager get-secret-value --secret-id $(SECRET_ID) | jq -r .SecretString > $(SECRET_FILE)

update-secret:
	aws secretsmanager update-secret --secret-id $(SECRET_ID) --secret-string file://$(SECRET_FILE)
