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
> rm -f .env
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

court_reserve/requirements.txt: Pipfile.lock
> pipenv lock --requirements > $@

.env: Makefile
> @echo "DRY_RUN=true" > $@
> @echo "DAYS_OFFSET=3" >> $@
> @echo "LOG_LEVEL=DEBUG" >> $@
> @echo "LOCAL_TIMEZONE=America/Los_Angeles" >> $@
> @echo "SECRET_ID=court_reserve_secret" >> $@

tmp/template.yaml: court_reserve/requirements.txt .env app.py $(shell find court_reserve -type f)
> mkdir -p $(@D)
> cdk synth --no-staging > $@

local-invoke: tmp/template.yaml
> function_name=$(shell yq eval '.Outputs.ExportlambdaCronFunctionName.Value.Ref' $<)
> sam local invoke "$${function_name}" --no-event --template-file $<
.PHONY: local-invoke

synth: court_reserve/requirements.txt app.py $(shell find court_reserve -type f)
> cdk synth
.PHONY: synth
