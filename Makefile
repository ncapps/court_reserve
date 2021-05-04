# https://tech.davis-hansson.com/p/make/
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c 
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >


SECRET_ID ?= court_reserve_secret

# Default - top level rule is what gets run when you just `make`
build:
> @echo "Building..."
.PHONY: build

clean:
> @echo "Cleaning..."
> rm -rf tmp
> rm -rf cdk.out
> rm -f court_reserve/requirements.txt
> rm -f template.yaml
.PHONY: clean

tmp/secret.json:
> mkdir -p $(@D)
> touch $@

tmp/.get-secret.sentinel: tmp/secret.json
> aws secretsmanager get-secret-value --secret-id $(SECRET_ID) | jq -r .SecretString > $<
> touch $@

tmp/.update-secret.sentinel: tmp/secret.json
> aws secretsmanager update-secret --secret-id $(SECRET_ID) --secret-string file://$<
> touch $@

get-secret: tmp/.get-secret.sentinel
.PHONY: get-secret

update-secret: tmp/.update-secret.sentinel
.PHONY: update-secret

local-invoke: tmp/template.yaml
> @echo "Running cron lambda locally..."
> function_name=$(shell yq eval '.Outputs.ExportlambdaCronFunctionName.Value.Ref' /tmp/template.yaml)
> @sam local invoke "$${function_name}" --no-event
.PHONY: local-invoke

tmp/template.yaml: $(shell find court_reserve -type f) app.py
> @mkdir -p $(@D)
> @pipenv lock --requirements > $(_PWD)/court_reserve/requirements.txt
> @cdk synth --no-staging > tmp/template.yaml 
	

synth:
> @echo "Synthesizng CloudFormation templates..."
> @pipenv lock --requirements > $(PWD)/court_reserve/requirements.txt
> @cdk synth
.PHONY: synth
