# Security

## Reporting a problem

If you find a security issue in this repository (a leaked secret, a way past the policy rules in
`code/src/agent/engineer/policy.py`, an injection path, an unsafe default), please report it privately:
open a private vulnerability report through the repository's **Security** tab ("Report a vulnerability"),
or contact the owner through the GitHub profile. Please do not open a public issue for it. I will
answer as soon as I can; this is a personal prototype, so there is no service-level promise.

## Credentials in this repository

- Every credential-like value in this repository is a **placeholder**: the `.env*.example` files,
  the docs, the test fixtures and the evidence logs. Real settings live in git-ignored files
  (`.env`, `.env.pdi`, `.secrets/`) that were never committed.
- ServiceNow instance names in the code, docs and evidence are placeholders (`dev000001` and similar).
  Test people and test tickets in the evidence are made up.
- Treat any key, token or password you might find in the history or in the team's base code as
  **compromised**: do not reuse it, and rotate your own keys before running this against anything real.
  If you deploy the system, generate fresh values for every secret in `code/.env.engineer.example`
  (operator secret, webhook token, database and Redis passwords, model and tracing keys).
- The scripts in `tools/` that talk to a ServiceNow instance read credentials from a local
  environment file. They were written for setup and testing; the agent itself never authenticates as an administrator.

## Scope and known limits

This is a prototype built and tested on a developer instance. It has not had an independent security
review. Known open items are listed in the README ("Status and limitations").
