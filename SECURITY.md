# Security and deployment boundaries

This release is designed for local research. Bind to 127.0.0.1 by default. A shared
local bearer token is required by the CLI for non-local binding, but is not a
substitute for enterprise authentication, role-based authorization or TLS. All
users with the shared token have prototype-level access to all imported stores.
Do not publish this API directly to the public Internet.

## Controls included

- Provider key is never sent to the browser or logged in reports.
- No arbitrary SQL, shell/code execution or external browsing tool is exposed to agents.
- Agent store scope is fixed outside the model. Function names and arguments are validated.
- Source media is served only through registered IDs and a runtime-directory allowlist.
- Explicit external-media consent and separate contributor-mode opt-in.
- Same-origin checks and local host checks; parameterized SQL; static-file separation.
- Filename sanitization through generated IDs, bounded uploads and file-type decoding.
- No facial recognition, identity attribution, or theft accusation workflow.
- Inventory writes, orders and model promotion are not accessible to either agent.

## Important remaining requirements

Raw media, responses and cached prompts are local files. They are not encrypted at
rest by this prototype. Set filesystem access controls, an approved retention and
deletion schedule, and encryption before using sensitive data. Do not upload
employer/customer information unless authorized. Standard-mode provider settings
are not a substitute for your organization's approval.

The browser's local API token is held in sessionStorage; close the tab/session and
clear it after use on a shared device. Generated summaries can still be wrong:
verify numeric tool outputs, source clips and human counts before taking action.

Model artifacts use joblib. Never load artifacts obtained from an untrusted source.
This release only creates local artifacts; it has no untrusted-model upload route.

Review `.gitignore`, `git status` and ZIP contents before publishing. Do not commit
`.env`, runtime files, real media, customer identities or credentials. The MIT
license does not grant rights to third-party video or provider model weights.
