# Security Policy

## Principles

- No credential ever enters: prompt artifacts, CodexTaskSpec, ResearchBundle, ExecutionReceipt, git diffs, or test fixtures.
- Research state truth: database plus immutable Artifact Store (SHA-256).
- Model output can only produce Proposals; tool execution produces Tool Evidence.
- Any accepted conclusion may be REVOKED by new evidence; history is never deleted.

## Reporting

Report security issues privately to the project maintainers. Do not open public issues for vulnerabilities.

## Supported scope

Synaisthesis is pre-alpha. Only the core platform repository is in scope.
