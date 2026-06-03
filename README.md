# analytics-engine-demo

Demo aplicație Python (api + worker) folosită pentru testarea variațiilor de stare
ZTA (`Alert` pentru api, `Failed_SupplyChain` pentru worker) și GUAC blast-radius
pe pachete pip.

## Componente

- `services/api/` — FastAPI: `/health`, `/aggregate` (count+sum), `/stats`
  (min/max/mean/stddev). Dependențe curente.
- `services/worker/` — process loop cu `cryptography==41.0.0` **intenționat
  vulnerabilă** pentru a forța failure pe strict SCA. Funcția pură
  `parse_tick_interval()` este extrasă pentru a fi testabilă.
- `.github/workflows/` — pipeline **modular** (orchestrator `ci-cd.yaml` +
  `job-*.yml`), identic ca structură cu `payments`, dar pentru Python.
- `requirements-dev.txt` — `pytest` + `httpx`, **doar pentru CI** (nu intră în imagini).
- `security-policy.yaml` — input pentru `policyAttestor-action`.
- `vex.json` — OpenVEX cu un statement `under_investigation`.

**Stare așteptată:**
- `analytics-api` → `Alert` (CVE-uri fixable tolerate cu `onVulnerabilityFound=Alert`).
- `analytics-worker` → `Failed_SupplyChain` (același CVE setup, dar `onVulnerabilityFound=Kill`).

## Pipeline modular (api + worker parametrizat)

`ci-cd.yaml` este un orchestrator subțire care apelează reusable workflows
(`job-*.yml`). Joburile per-serviciu (`build-push`, `scan-image`, `attestations`,
`sign`) sunt **parametrizate** și apelate de **două ori** (api/worker) printr-un
input `service` — deci o singură definiție per etapă, fără duplicare.

Ordinea: `build-metadata` (py_compile) + `unit-tests` (pytest, **poartă** build-ul)
+ `security-scan` (gitleaks/Semgrep/checkov pe sursă — gitleaks **BLOCANT**, poartă
build-ul) → `build-push` → `scan-image` (Trivy `trivy-action@v0.36.0`) →
`attestations` (SBOM/OpenVEX/VBBI/ZTA-policy + **`security-scan/v1`** via
`SabinGhost19/security-scan-attestorAction@v1.0.1`) + `slsa-provenance` → `sign` →
`bump-manifests`. `security-scan` rulează o singură dată pe tot repo-ul (un secret
oriunde blochează ambele imagini); atestarea `security-scan/v1` se semnează per-imagine
în `job-attestations.yml`. Primul pas din fiecare job este `harden-runner` (audit, fixat pe SHA).

**Identități keyless** (de pus în `trustedIssuers`):

```text
https://github.com/SabinGhost19/analytics-engine-demo/.github/workflows/job-attestations.yml@refs/heads/main
https://github.com/SabinGhost19/analytics-engine-demo/.github/workflows/job-sign.yml@refs/heads/main
```

## Teste locale

```bash
pip install -r services/api/requirements.txt -r requirements-dev.txt
( cd services/api && pytest -q )
( cd services/worker && pytest -q )
```

## Setup

Pipeline-ul folosește **același repo de manifeste** ca `payments-api-demo` și
`demo-app`: `SabinGhost19/vulfastapi-manifests-samples` (oglindit local ca
`manifests-demo-app/`). Sub-path-ul în acel repo este `analytics-engine/`.

1. Creează repo-ul source:

   ```bash
   gh repo create SabinGhost19/analytics-engine-demo --public --source=. --remote=origin
   ```

2. Secrete identice cu `payments-api-demo`:

   ```bash
   gh secret set VBBI_HMAC_KEY --body "<same>"
   gh secret set MANIFESTS_REPO_TOKEN --body "<PAT>"
   ```

3. Adaugă manifestele în repo-ul shared:

   ```bash
   cd vulfastapi-manifests-samples
   mkdir -p analytics-engine/api analytics-engine/worker
   cp ../customCRD/demo-repos-apps/manifests-demo-app/analytics-engine/sca-relaxed.yaml ./analytics-engine/
   cp ../customCRD/demo-repos-apps/manifests-demo-app/analytics-engine/sca-strict.yaml ./analytics-engine/
   cp ../customCRD/demo-repos-apps/manifests-demo-app/analytics-engine/api/zta-api.yaml ./analytics-engine/api/
   cp ../customCRD/demo-repos-apps/manifests-demo-app/analytics-engine/worker/zta-worker.yaml ./analytics-engine/worker/
   git add -A && git commit -m "add analytics-engine manifests" && git push
   ```

4. Push source repo + apply în cluster (vezi README payments pentru detalii).

Manifestele includ **2 SCA-uri** (relaxed + strict), una per microserviciu. Aplică
**ambele** SCA-uri înainte de ZTA-uri. SCA-urile listează deja identitățile
`job-attestations.yml` + `job-sign.yml`.

**IMPORTANT**: pachetele Python pinned-vulnerable sunt intenționate. Nu le
actualiza — constituie cazul de demo `Failed_SupplyChain`. Imaginea **nu se rulează
niciodată în production**.
