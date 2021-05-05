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

DRY_RUN ?= false
DAYS_OFFSET ?= 3
LOG_LEVEL ?= DEBUG
SECRET_ID ?= court_reserve_secret

# Default - top level rule is what gets run when you just `make`
build: court_reserve/requirements_lock.txt .env app.py
> cdk synth
.PHONY: build

clean:
> @echo "Cleaning..."
> rm -rf tmp
> rm -rf cdk.out
> rm -f court_reserve/requirements_lock.txt
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

court_reserve/requirements_lock.txt: court_reserve/requirements.txt
> pip freeze > $@

.env: Makefile
> @echo DRY_RUN=$(DRY_RUN) > $@
> @echo DAYS_OFFSET=$(DAYS_OFFSET) >> $@
> @echo LOG_LEVEL=$(LOG_LEVEL) >> $@
> @echo SECRET_ID=$(SECRET_ID) >> $@
> @echo LOCAL_TIMEZONE=America/Los_Angeles >> $@

tmp/template.yaml: court_reserve/requirements_lock.txt .env app.py $(shell find court_reserve -type f)
> mkdir -p $(@D)
> cdk synth --no-staging > $@

local-invoke: tmp/template.yaml
> function_name=$(shell yq eval '.Outputs.ExportlambdaCronFunctionName.Value.Ref' $<)
> sam local invoke "$${function_name}" --no-event --template-file $<
.PHONY: local-invoke
