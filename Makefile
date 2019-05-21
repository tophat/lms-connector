BUILD_DIR?=build
JUNITXML_PATH?=$(BUILD_DIR)/reports/test_results.xml
SERVERLESS=./node_modules/serverless/bin/serverless
STAGE?=development
AWS_REGION?=us-east-1

.PHONY: clean
clean:
	rm -rf node_modules $(BUILD_DIR)
	find . -regex "\(.*__pycache__.*\|*.py[co]\)" -delete

.PHONY: deploy
deploy: clean node_modules
	$(SERVERLESS) create_domain --stage $(STAGE) --region $(AWS_REGION)
	$(SERVERLESS) deploy --stage $(STAGE) --region $(AWS_REGION)

node_modules:
	yarn install

package: node_modules
	$(SERVERLESS) package -p $(BUILD_DIR)/package

.PHONY: pipenv
pipenv:
	pipenv install --dev

.PHONY: pipenv
run:
	pipenv run ./manage.py runserver 9284 --verbosity 3

.PHONY: test
test: pipenv
	pipenv run pytest --junitxml=$(JUNITXML_PATH) lms_connector/tests

.PHONY: pep8
pep8: pipenv
	pipenv run pytest --codestyle lms_connector/
