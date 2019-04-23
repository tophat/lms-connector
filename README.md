# lms-connector

[![CircleCI](https://circleci.com/gh/tophat/lms-connector.svg?style=svg)](https://circleci.com/gh/tophat/lms-connector)
[![codecov](https://codecov.io/gh/tophat/lms-connector/branch/master/graph/badge.svg)](https://codecov.io/gh/tophat/lms-connector)

### Deploy

To deploy this service, push to master.

### Running tests
`make test`

### Start Server
`make run`

### Secret management
Use ssm parameter store.

### Add additional AWS resources
Additional resources can be added to the generated cloudformation.yml file.

### Securing the service
Lockdown with IAM and use a new KMS key for this service.

### Notes
The serverless plugin that creates Route53 records does so outside of CloudFormation. Be sure to delete these records
when cleaning up dev CloudFormation stacks.
