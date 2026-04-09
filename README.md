<p align="center"><img src="qbtc_logo.png" width="120" alt="Proofnet BTC"></p>

# Proofnet BTC SDK (MIT)

Client helpers and examples for building against a local Proofnet BTC node.

All SDK traffic routes through **BTCore** on port `8788`:

- Proofnet Core: `http://127.0.0.1:8788/pwos/proofnet`
- ProofWallet: `http://127.0.0.1:8788/pwos/wallet`
- BTCore (read lane): `http://127.0.0.1:8788`

## Architecture

- **8788** — BTCore HTTP read lane. The standard SDK/app entry point.
- **3006** — BTCore PQTLS/TLS lane. Encrypted transport.

Apps use the BTCore-routed paths on `8788`. The gateway handles routing, access control, and service discovery.

## Core API quick map (via BTCore)

- Node status: `GET /pwos/proofnet/api/status`
- Core chain snapshot: `GET /pwos/proofnet/core/info`, `GET /pwos/proofnet/core/block/tip`, `GET /pwos/proofnet/core/assets`
- Memory Blocks SPV: `GET /pwos/proofnet/mblk/spv/proof?digest=...`, `POST /pwos/proofnet/mblk/spv/proofs`
- Variant Nova (read-only local snapshot): `GET /pwos/proofnet/vnova/prices`, `GET /pwos/proofnet/vnova/price`, `GET /pwos/proofnet/vnova/health`, `GET /pwos/proofnet/vnova/overview`
- Blockie AI (repo-local grounding): `POST /pwos/proofnet/ai/chat`, `GET /pwos/proofnet/ai/docs/search`, `GET /pwos/proofnet/ai/qbit/context`

## Python quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./python
python examples/proofnet_status.py
```

## JavaScript/TypeScript (Node/Next.js) quickstart

```bash
node -e 'import { getApiStatus, resolveCoreBaseUrl } from "@proofnet/sdk"; const base=resolveCoreBaseUrl(); getApiStatus(base).then(r=>console.log(r.status, r.data)).catch(console.error)'
```

## Curl (no SDK)

```bash
curl -s http://127.0.0.1:8788/pwos/proofnet/api/status | jq
curl -s http://127.0.0.1:8788/pwos/proofnet/core/info | jq
curl -s 'http://127.0.0.1:8788/pwos/proofnet/ai/docs/search?q=proofnet%20core%20facts' | jq
curl -s http://127.0.0.1:8788/pwos/wallet/readyz | jq
curl -s http://127.0.0.1:8788/healthz | jq
```
