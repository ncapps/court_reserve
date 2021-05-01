.PHONY: get-secret update-secret

_PWD = $(shell pwd)
_MKDIR = $(shell mkdir -p)
SECRET_ID = court_reserve_secret
DOWNLOADS_PATH = $(_PWD)/tmp
SECRET_FILE = config.json
SECRET_PATH = $(DOWNLOADS_PATH)/$(SECRET_FILE)

export SECRET_ID
export SECRET_FILE

$(shell mkdir --parents $(DOWNLOADS_PATH))

.PHONY: get-secret, update-secret, clean, deploy

get-secret:
	@echo "Downloading secret..."
	@aws secretsmanager get-secret-value --secret-id $(SECRET_ID) | jq -r .SecretString > $(SECRET_PATH)

update-secret:
	@echo "Updating secret in Secrets Manager"
	@aws secretsmanager update-secret --secret-id $(SECRET_ID) --secret-string file://$(SECRET_PATH)

run-local:
	python court_reserve/court_reserve.py

clean:
	@echo "Cleaning..."
	@-rm -rf $(DOWNLOADS_PATH)

synth:
	@echo "Synthesizng CloudFormation templates..."
	@pipenv lock --requirements > $(PWD)/court_reserve/requirements.txt
	@cdk synth

deploy:
	@echo "Deploying to the cloud!"
	@cdk deploy
