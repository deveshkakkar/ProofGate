# Security and vulnerability reports

ProofGate is a local research prototype. It has no supported production release, hosted service, or security response-time commitment.

## Scope

The formal properties cover the pure credit-admission function. They do not prove the security of the HTTP server, compiler, database, evaluator, or host.

The frozen experiment uses bubblewrap to restrict filesystem and process visibility, while sharing host networking. The evaluator and supervisor are trusted. Run the demonstration in a dedicated Linux environment and keep its API bound to loopback. See [architecture and trust boundaries](docs/architecture.md) for details.

## Reporting a problem

For a correctness bug with no sensitive details, [open an issue](https://github.com/deveshkakkar/ProofGate/issues/new) with the commit, reproduction command, expected behavior, and relevant error output.

For a vulnerability or exposed credential, use **Security → Report a vulnerability** if that option is available. Otherwise, open an issue asking the maintainer for a private reporting channel and omit the exploit details and sensitive material. Do not attach credentials, private prompts, authentication files, or unrelated host data to a public issue.

Useful reports identify whether the problem concerns a proved property, a runtime check, the trusted evaluator, or deployment of the accepted artifact. A passing recorded experiment is not a security certification.
