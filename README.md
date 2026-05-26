# analytics-engine-demo

Demo aplicație Python (api + worker) folosită pentru testarea variațiilor
de stare ZTA (`Alert` pentru api, `Failed_SupplyChain` pentru worker) și
GUAC blast-radius pe pachete pip.

## Componente

- `services/api/` — FastAPI (`/health`, `/aggregate`). Dependențe curente.
- `services/worker/` — process loop cu `cryptography==41.0.0` **intenționat
  vulnerabilă** pentru a forța failure pe strict SCA.
- `.github/workflows/ci-cd.yaml` — același pattern ca payments, dar pentru
  Python.
- `security-policy.yaml` — input pentru `policyAttestor-action`.
- `vex.json` — OpenVEX cu un statement `under_investigation`.

**Stare așteptată:**
- `analytics-api` → `Alert` (CVE-uri fixable tolerate cu `onVulnerabilityFound=Alert`).
- `analytics-worker` → `Failed_SupplyChain` (același CVE setup, dar `onVulnerabilityFound=Kill`).

## Setup

Pipeline-ul folosește **același repo de manifeste** ca `payments-api-demo`
și `demo-app`: `SabinGhost19/vulfastapi-manifests-samples` (oglindit local
ca `demo-app-manifests-samples/`). Sub-path-ul în acel repo este
`analytics-engine/`.

1. Creează repo-ul source:

   ```bash
   gh repo create SabinGhost19/analytics-engine-demo --public --source=. --remote=origin
   ```

2. Secret-uri identice cu `payments-api-demo`:

   ```bash
   gh secret set VBBI_HMAC_KEY --body "<same>"
   gh secret set MANIFESTS_REPO_TOKEN --body "<PAT>"
   ```

3. Adaugă manifestele în repo-ul shared:

   ```bash
   cd vulfastapi-manifests-samples
   mkdir -p analytics-engine/api analytics-engine/worker
   cp ../customCRD/demo-app-manifests-samples/analytics-engine/sca-relaxed.yaml ./analytics-engine/
   cp ../customCRD/demo-app-manifests-samples/analytics-engine/sca-strict.yaml ./analytics-engine/
   cp ../customCRD/demo-app-manifests-samples/analytics-engine/api/zta-api.yaml ./analytics-engine/api/
   cp ../customCRD/demo-app-manifests-samples/analytics-engine/worker/zta-worker.yaml ./analytics-engine/worker/
   git add -A && git commit -m "add analytics-engine manifests" && git push
   ```

4. Push source repo + apply în cluster (vezi README payments pentru detalii).

Manifestele includ **2 SCA-uri** (relaxed + strict), una per microserviciu.
Aplică **ambele** SCA-uri înainte de ZTA-uri.

**IMPORTANT**: pachetele Python pinned-vulnerable sunt intenționate. Nu le
actualiza — constituie cazul de demo `Failed_SupplyChain`. Imaginea **nu se
rulează niciodată în production**.
