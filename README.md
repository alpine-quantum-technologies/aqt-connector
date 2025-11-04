# aqt-connector

[![License](https://img.shields.io/github/license/alpine-quantum-technologies/aqt-connector.svg?)](https://opensource.org/licenses/Apache-2.0) 

<img width="300px" alt="AQT logo" src="https://www.aqt.eu/wp-content/uploads/2025/07/Logo-AQT-Alpine-Quantum-Technologies.svg">

An SDK and lightweight CLI to authenticate with AQT's Arnica platform using OIDC (Auth0).

It supports:

- Device Authorization Flow (QR code + verification URL)
- Client Credentials Flow (machine-to-machine)
- Local token storage and verification against JWKS
- Simple Python API and a small CLI (via python -m aqt_connector)

Unless you were explicitly sent here, you probably want to instead use an AQT provider for another library, where this library
has already been integrated. We already have those for:
- Qiskit: https://github.com/qiskit-community/qiskit-aqt-provider
- Cirq: https://github.com/quantumlib/Cirq/tree/main/cirq-aqt
- Pennylane: https://github.com/PennyLaneAI/pennylane-aqt



## Requirements

- Python >= 3.9, < 3.14


## Installation

```bash
pip install aqt-connector
```


## Quickstart

### Python API

```python
from aqt_connector import ArnicaApp, ArnicaConfig, log_in, get_access_token

# Configure (use client credentials OR device flow)
config = ArnicaConfig()

# Option A: client credentials
# config.client_id = "YOUR_CLIENT_ID"
# config.client_secret = "YOUR_CLIENT_SECRET"

# Option B: device flow (no client credentials set)

# Optional: change base API URL
# config.arnica_url = "https://arnica.aqt.eu/api"

app = ArnicaApp(config)

# Acquire token (stored by default when obtained)
token = log_in(app)
print("Access token:", token[:10] + "…")

# Later, get current token (if still valid and stored)
maybe_token = get_access_token(app)
```

### CLI: log in

The CLI is exposed via the module entry point. Run:

```bash
python -m aqt_connector --help
python -m aqt_connector log-in
```

By default, this starts the device flow and prints a QR code and verification URL. Once you complete the flow in your browser, an ID token is obtained, verified, and stored locally.

You can also provide client credentials (machine-to-machine):

```bash
python -m aqt_connector log-in \
    --client-id YOUR_CLIENT_ID \
    --client-secret YOUR_CLIENT_SECRET
```

Optional override of the Arnica API URL:

```bash
python -m aqt_connector log-in --arnica-url https://arnica.aqt.eu/api
```

Where are things stored?

- When using the CLI, configuration and the token are stored in your OS application directory for "aqt" (e.g. Linux: ~/.config/aqt; macOS: ~/Library/Application Support/aqt; Windows: %APPDATA%\aqt).
- The token is saved as a file named access_token in that directory.


## Configuration

The SDK loads configuration from two places, in this order of precedence (last wins):

1. A local config file at {app_dir}/config
2. Environment variables prefixed with AQT_

app_dir defaults to:

- Library usage (Python API): ~/.aqt
- CLI usage: your OS app directory for "aqt" (see Quickstart)

### Config file (TOML)

Create a file named config in the app_dir or a custom location which you then pass to the ArnicaConfig (`config = ArnicaConfig("~/myconfig")`). TOML dotted keys or tables are supported. Example:

```toml
[default]
arnica_url = "https://arnica.aqt.eu/api"
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
store_access_token = true
```

Notes:

- store_access_token=true will persist the obtained token to {app_dir}/access_token
- To disable persistence, set store_access_token=false in this file

### Environment variables

Environment variables use the AQT_ prefix and map to the same lowercase keys. Examples:

- AQT_ARNICA_URL
- AQT_CLIENT_ID
- AQT_CLIENT_SECRET
- AQT_STORE_ACCESS_TOKEN

Tip: Prefer the config file to disable persistence reliably (see notes above).

## Testing

Install the dependencies

```bash
uv sync --group test
```

Unit tests:

```bash
pytest -q tests/commit
```

Integration tests (require Auth0 test credentials and a browser via Playwright):

```bash
# Required environment variables
# AUTH0_TEST_TENANT_DOMAIN
# AUTH0_TEST_CLIENT_CREDENTIALS_AUDIENCE
# AUTH0_TEST_CLIENT_CREDENTIALS_CLIENT_ID
# AUTH0_TEST_CLIENT_CREDENTIALS_CLIENT_SECRET
# AUTH0_TEST_DEVICE_FLOW_CLIENT_ID
# AUTH0_TEST_DEVICE_FLOW_USER_EMAIL
# AUTH0_TEST_DEVICE_FLOW_USER_PASSWORD

pytest -q tests/integration
```


## Contributing

Issues and PRs are welcome. For local development, we use UV  to manage virtual environments and install the package:

```bash
uv sync  # includes dev tools by default
```

Run linters and tests before submitting changes.

```bash
uvx pyproject-fmt pyproject.toml --check
uvx ruff check
uvx typos
uvx ruff format --check
uv run mypy .
```


## License

Copyright (c) Alpine Quantum Technologies GmbH.

This software is licensed under the Apache License 2.0. See the [LICENSE file](LICENSE) for details.