# lms-connector
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors)

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

## Contributors

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore -->
<table><tr><td align="center"><a href="http://codesamplez.com"><img src="https://avatars3.githubusercontent.com/u/368209?v=4" width="100px;" alt="Rana Md Ali Ahsan"/><br /><sub><b>Rana Md Ali Ahsan</b></sub></a><br /><a href="#infra-ranacseruet" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/tophat/lms-connector/commits?author=ranacseruet" title="Documentation">📖</a></td></tr></table>

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!