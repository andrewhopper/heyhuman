# EXPERIMENTAL CODE. Do not use in production.
# File UUID: 9a5c2e71-4b38-4d6f-8e10-b3f7d1a6c259
PROFILE ?= default
REGION ?= us-east-1
EMAIL ?=
CDK = cd infra/cdk && npx --yes aws-cdk@2

.PHONY: install test synth bootstrap deploy destroy outputs smoke

install:
	python3 -m pip install -r infra/cdk/requirements.txt -r requirements-dev.txt

test:
	python3 -m pytest -q tests packages/mcp-server/tests

synth:
	$(CDK) synth --quiet

bootstrap:
	$(CDK) bootstrap --profile $(PROFILE) --region $(REGION)

deploy: test
	$(CDK) deploy --profile $(PROFILE) --require-approval broadening \
		$(if $(EMAIL),-c alertEmail=$(EMAIL)) --outputs-file ../../outputs.json

outputs:
	@python3 -c "import json;o=list(json.load(open('outputs.json')).values())[0];[print(f'{k}={v}') for k,v in o.items()]"

smoke:
	HEYHUMAN_AGENT_URL=$$(python3 -c "import json;print(list(json.load(open('outputs.json')).values())[0]['AgentUrl'])") \
	AWS_PROFILE=$(PROFILE) AWS_REGION=$(REGION) python3 cli/heyhuman.py ask --html tests/browser/tictactoe.html \
		--message "Smoke test: tap any square" --ttl 300 --timeout 300

destroy:
	$(CDK) destroy --profile $(PROFILE) --force
