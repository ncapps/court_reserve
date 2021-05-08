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
build: .env
> cdk synth
.PHONY: build

clean:
> @echo "Cleaning..."
> rm -rf tmp
> rm -rf cdk.out
> rm -f .env
.PHONY: clean

tmp/secret.json:
> mkdir --parents $(@D)
> touch $@

tmp/.get_secret.sentinel: tmp/secret.json
> aws secretsmanager get-secret-value --secret-id $(SECRET_ID) | jq -r .SecretString > $<
> touch $@

tmp/.update_secret.sentinel: tmp/secret.json
> aws secretsmanager update-secret --secret-id $(SECRET_ID) --secret-string file://$<
> touch $@

get-secret: tmp/.get-secret.sentinel
.PHONY: get-secret

update-secret: tmp/.update-secret.sentinel
.PHONY: update-secret

# Freeze only requirements in requirement.txt
court_scheduler/court_reserve_lambda/requirements_lock.txt: court_scheduler/court_reserve_lambda/requirements.txt
> pip freeze --requirement $< | grep --before-context=200 "pip freeze" | grep --invert-match "pip freeze" > $@

.env: Makefile
> @echo DRY_RUN=$(DRY_RUN) > $@
> @echo DAYS_OFFSET=$(DAYS_OFFSET) >> $@
> @echo LOG_LEVEL=$(LOG_LEVEL) >> $@
> @echo SECRET_ID=$(SECRET_ID) >> $@
> @echo LOCAL_TIMEZONE=America/Los_Angeles >> $@

tmp/.court_reserve_lambda.sentinel: app.py court_scheduler/court_reserve_lambda/requirements_lock.txt \
  $(shell find court_scheduler -type f) build

tmp/template.yaml: tmp/.court_reserve_lambda.sentinel
> mkdir --parents $(@D)
> cdk synth CourtSchedulerPipeline/Prod/CourtReserve --no-staging > $@

local-invoke: tmp/template.yaml
> function_name=$(shell yq eval '.Outputs.ExportlambdaCronFunctionName.Value.Ref' $<)
> sam local invoke "$${function_name}" --no-event --template-file $<
.PHONY: local-invoke

deploy-pipeline: .env
> cdk deploy
.PHONY: deploy-pipeline
