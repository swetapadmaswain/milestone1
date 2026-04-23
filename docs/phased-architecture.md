Below is a phase-wise architecture you can paste into docs/phased-architecture.md.

# Phase-Wise Architecture: AI-Powered Restaurant Recommendation System
## Overview
This architecture delivers the recommendation system incrementally: start with reliable data and deterministic filtering, then add LLM reasoning, personalization, and production hardening.  
Each phase is independently testable and deployable.
---
## Phase 1: Foundation (Data + Baseline Recommendations)
### Goal
Build a working end-to-end system using structured filtering only (no LLM dependency in final ranking yet).
### Components
- **Dataset Ingestion Service**
  - Load dataset from Hugging Face
  - Persist raw snapshot for reproducibility
- **Data Preparation Pipeline**
  - Clean nulls, normalize location/cuisine/cost/rating
  - Standardize categorical values (e.g., cuisine aliases)
- **Restaurant Catalog Store**
  - Structured storage (CSV/Parquet/SQLite/Postgres)
  - Indexed on location, cuisine, budget, rating
- **Preference Input API/UI**
  - Basic web UI is the primary source of user input in Phase 1
  - Collect location, budget, cuisine, min rating, optional constraints
- **Rule-Based Filter Engine**
  - Deterministic matching and scoring
  - Return top-N restaurants
### Output
- Ranked recommendations with core fields (name, cuisine, rating, cost)
### Success Criteria
- Users receive relevant candidates in <1–2 sec
- Data quality checks pass (missing/invalid field thresholds)
---
## Phase 2: LLM-Augmented Ranking and Explanations
### Goal
Improve quality and transparency by adding LLM reasoning over filtered candidates.
### Components
- **Prompt Builder**
  - Inject user preferences + filtered candidates into structured prompt
  - Include strict output schema (JSON) for reliability
- **LLM Orchestrator**
  - Calls LLM API
  - Retries, timeout, and fallback to rule-based ranker on failure
- **Response Parser/Validator**
  - Validate JSON schema
  - Sanitize hallucinated values (must match known candidates)
- **Explanation Generator**
  - Produce concise “why this fits” reasoning per restaurant
  - Optionally include trade-offs (budget vs rating, distance vs cuisine)
### Output
- Top recommendations with AI explanation and confidence tags
### Success Criteria
- Explanations are concise, preference-aware, and fact-grounded
- Zero invalid output shown to users (schema validation enforced)
---
## Phase 3: Personalization and Learning Loop
### Goal
Continuously improve recommendation relevance from user behavior.
### Components
- **Feedback Capture**
  - Explicit: likes/dislikes, thumbs up/down
  - Implicit: clicks, dwell time, conversion signals
- **User Profile Service**
  - Preference history (e.g., favored cuisines, budget bands)
  - Optional session-level personalization
- **Hybrid Ranking Engine**
  - Combine rule score + LLM score + personalization score
- **Experimentation Layer**
  - A/B tests for prompts, weights, and ranking strategies
### Output
- Personalized recommendations improving over repeated interactions
### Success Criteria
- Measurable improvement in CTR/engagement vs non-personalized baseline
- Stable ranking quality across major cities/cuisines
---
## Phase 4: Production Readiness (Scalability, Reliability, Governance)
### Goal
Harden system for real-world usage.
### Components
- **API Gateway + Auth (if needed)**
  - Rate limiting, request validation
- **Caching Layer**
  - Cache common query + candidate sets
  - Optional cache for LLM explanations
- **Monitoring and Observability**
  - Latency, error rates, LLM token usage/cost, fallback frequency
- **Quality/Safety Guardrails**
  - Prompt/response safety checks
  - PII protection and logging policy
- **CI/CD + Model/Prompt Versioning**
  - Reproducible deployments
  - Rollback for prompt or model regressions
### Output
- Stable, observable, cost-controlled recommendation platform
### Success Criteria
- SLOs met (availability, latency)
- Controlled inference costs with no major quality regression
---
## Logical Architecture (Cross-Phase)
1. **User Interface** (Web/App/Chat)
2. **Preference API**
3. **Filtering Service** (structured retrieval)
4. **LLM Reasoning Service** (ranking + explanations)
5. **Recommendation Aggregator** (merge + final order)
6. **Data Stores**
   - Restaurant catalog
   - User profile/feedback
   - Logs/metrics
7. **Observability & Governance** (monitoring, safety, audit)
---
## Data Flow
1. User submits preferences.
2. Filtering service retrieves candidate restaurants from catalog.
3. Candidates + preferences are sent to LLM reasoning service.
4. LLM returns ranked options + explanations (validated).
5. Aggregator prepares final response.
6. UI displays recommendations.
7. User feedback is stored and used to improve future ranking.
---
## Non-Functional Requirements
- **Performance:** sub-2s response for filtered results; graceful degradation if LLM is slow
- **Reliability:** fallback path when LLM fails
- **Transparency:** every recommendation includes rationale
- **Scalability:** stateless services + indexed queries + caching
- **Cost Control:** token budgeting, candidate cap, caching, model selection policy
- **Security/Privacy:** minimal personal data collection; secure API keys
---
## Suggested Tech Stack (Optional)
- **Data:** Pandas + Parquet / Postgres
- **Backend:** FastAPI/Flask
- **LLM Integration:** OpenAI/other LLM via API wrapper
- **Frontend:** Streamlit/React
- **Observability:** Prometheus/Grafana or cloud-native monitoring
- **Deployment:** Docker + CI/CD pipeline

---

## Detailed Edge Cases and Risk Handling

### Phase 1: Foundation (Data + Baseline Recommendations)
- **Dataset schema drift:** Source columns are renamed/removed across versions.
  - Mitigation: enforce schema checks and maintain a mapping layer with fail-fast errors.
- **Missing critical fields:** Many rows lack location/cuisine/rating/cost.
  - Mitigation: define per-field handling (`drop`, `impute`, `unknown`) and track quality thresholds.
- **Location normalization conflicts:** `Bangalore`, `Bengaluru`, abbreviations, casing, spacing.
  - Mitigation: canonical location dictionary + deterministic normalization.
- **Cuisine ambiguity:** Multi-cuisine and alias patterns (e.g., `Indo-Chinese` vs `Chinese`).
  - Mitigation: multi-label parsing and alias mapping.
- **Cost format inconsistency:** Numeric, ranges, symbols, or varying units.
  - Mitigation: parse into normalized numeric representation and standard unit policy.
- **Rating parsing issues:** `NEW`, `N/A`, text-based rating formats, out-of-range values.
  - Mitigation: strict parser and bounded validation.
- **Duplicate entities:** Same restaurant appears under slight naming/address differences.
  - Mitigation: dedupe strategy with confidence-based merge rules.
- **No-result strict filters:** User constraints can produce zero matches.
  - Mitigation: controlled relaxation strategy with transparent fallback messaging.

### Phase 2: LLM-Augmented Ranking and Explanations
- **Prompt token overflow:** Candidate payload exceeds model context limits.
  - Mitigation: candidate pre-ranking/top-K cap and compact prompt schema.
- **Invalid LLM output format:** Malformed or non-JSON responses.
  - Mitigation: schema validation + repair/retry + fallback to deterministic ranking.
- **Hallucinated recommendations:** LLM outputs restaurants not in filtered candidates.
  - Mitigation: ID-based candidate contract; reject unknown entities.
- **Constraint violations in ranking:** LLM ignores hard filters (budget/rating/location).
  - Mitigation: enforce hard constraints pre/post LLM.
- **Factually incorrect explanations:** Narrative contradicts rating/cost/cuisine fields.
  - Mitigation: post-generation fact-grounding checks.
- **Latency and reliability failures:** API timeout, 429s, transient provider errors.
  - Mitigation: retries with backoff, timeout budgets, and fallback orchestration.
- **Prompt injection via input fields:** User text attempts to override system instructions.
  - Mitigation: sanitize user text, isolate instructions, and enforce strict output schema.
- **Unsafe explanation content:** Toxic/biased/inappropriate output.
  - Mitigation: moderation filtering and safe fallback templates.

### Phase 3: Personalization and Learning Loop
- **Cold start users:** No historical preferences.
  - Mitigation: use session intent + city-level baseline ranking.
- **Sparse explicit feedback:** Limited likes/dislikes for model tuning.
  - Mitigation: blend implicit signals with confidence weighting.
- **Noisy implicit signals:** Dwell/clicks do not always imply positive intent.
  - Mitigation: robust signal weighting and outlier handling.
- **Preference drift:** User tastes change over time.
  - Mitigation: time-decayed profiles and session-priority ranking.
- **Conflicting history vs current query:** Past behavior disagrees with active constraints.
  - Mitigation: current session hard constraints override historical soft preferences.
- **Popularity bias feedback loop:** Same popular restaurants dominate exposure.
  - Mitigation: controlled exploration and diversity constraints.
- **Experiment contamination:** Users are exposed to multiple A/B variants.
  - Mitigation: sticky assignment and strict experiment metadata governance.
- **Segment instability:** Quality differs between metros and low-density regions.
  - Mitigation: segment-level monitoring and guardrail metrics.

### Phase 4: Production Readiness (Scalability, Reliability, Governance)
- **Cache staleness:** Updated catalog not reflected in responses.
  - Mitigation: TTL strategy + event-driven invalidation.
- **Cache key explosion:** High-cardinality query combinations consume resources.
  - Mitigation: normalized keys, bounded cache sizes, and eviction policies.
- **Traffic spikes:** Meal-time bursts increase latency and error rates.
  - Mitigation: autoscaling + queue protection + graceful degradation modes.
- **Partial dependency outages:** LLM or DB failure impacts one stage only.
  - Mitigation: health-aware routing and deterministic fallback path.
- **Cost overruns:** Token usage grows with volume and prompt size.
  - Mitigation: token budgets, candidate caps, and per-request cost telemetry.
- **Model/prompt regression:** New version lowers recommendation quality.
  - Mitigation: canary rollout + offline evals + one-click rollback.
- **Observability blind spots:** Poor visibility into recommendation quality failures.
  - Mitigation: track relevance metrics (CTR, save rate, fallback rate, complaint rate).
- **Abuse patterns:** Bot-like high-frequency API usage.
  - Mitigation: rate limits, anomaly detection, and abuse throttling.

### Cross-Phase Must-Test Scenarios
- **Boundary outcomes:** zero candidates, one candidate, and very large candidate sets.
- **Input ambiguity:** city typos, colloquial localities, mixed-language cuisine names.
- **Reproducibility checks:** stable ranking under identical inputs (within defined variance).
- **Fallback correctness:** useful results and clear messaging when LLM is unavailable.
- **Explanation grounding:** generated rationale must not contradict structured data.
- **SLO under failure:** latency/error targets validated during degraded modes.

---

## Edge Case Test Case Template

Use this template to convert each edge case into an executable test.

| Test ID | Phase | Category | Preconditions | Input | Steps | Expected Result | Priority | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|
| EC-XXX | P1/P2/P3/P4 | Data/LLM/Personalization/Prod | Required setup/state | User request or system event | Numbered execution steps | Functional + non-functional outcomes | P0/P1/P2 | Team/Person | Not Started/In Progress/Done |

### Field Guidance
- **Test ID:** Keep a stable identifier (`EC-P2-007`) for traceability.
- **Phase:** Map directly to architecture phase where behavior is implemented.
- **Category:** Helps route failures to the right subsystem owner.
- **Preconditions:** Include dataset version, feature flags, model version, cache state, and test user profile.
- **Input:** Prefer exact payload (location, budget, cuisine, min rating, constraints).
- **Steps:** Keep deterministic; include API/UI path and fallback simulation where relevant.
- **Expected Result:** Define both output correctness and system behavior (latency, fallback, logging).
- **Priority:** `P0` for user-visible failures and data integrity risks.

### Minimal Evidence Checklist (per executed test)
- Request payload and timestamp captured.
- Response payload and rank order captured.
- Fallback flag recorded (if used).
- Relevant logs/metrics snapshot attached (latency, retries, error code).
- Pass/fail verdict with defect link (if failed).

## Sample Edge Case Test Cases

| Test ID | Phase | Category | Preconditions | Input | Steps | Expected Result | Priority | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|
| EC-P1-001 | P1 | Data | Ingestion job points to latest dataset snapshot | Dataset with renamed `estimated_cost` column | 1) Run ingestion 2) Run schema validation | Job fails fast with clear schema error and mapping hint; no partial corrupt load | P0 | Data Eng | Not Started |
| EC-P1-004 | P1 | Filtering | Catalog loaded; strict filter mode enabled | Location=small city, Budget=low, Cuisine=rare, Min rating=4.5 | 1) Submit preferences 2) Execute filter | No silent empty screen; system returns "no match" explanation and relaxed alternatives | P0 | Backend | Not Started |
| EC-P2-003 | P2 | LLM Output | LLM endpoint reachable; validator enabled | Normal user query with 30 candidates | 1) Force malformed JSON response from LLM 2) Process result | Parser rejects invalid output, retry occurs, then deterministic fallback if retries fail | P0 | AI Platform | Not Started |
| EC-P2-006 | P2 | Safety | Prompt sanitization enabled | Additional preference includes prompt-injection text | 1) Submit crafted input 2) Run recommendation flow | Injection text treated as plain data; policy/system instructions remain intact; valid grounded output returned | P0 | AI Platform | Not Started |
| EC-P3-002 | P3 | Personalization | Test user has no history | First-time user query | 1) Request recommendations 2) Review ranking source | System uses session intent + city baseline; no personalization-only dependency failure | P1 | Reco Team | Not Started |
| EC-P3-005 | P3 | Personalization | User profile favors expensive dining; session says low budget | Budget=low with prior high-budget history | 1) Submit query 2) Compare ranked results | Session hard constraints override historical preferences; returned options stay within low budget | P0 | Reco Team | Not Started |
| EC-P4-003 | P4 | Reliability | LLM service intentionally unavailable | Standard user request | 1) Trigger LLM outage 2) Request recommendations | Deterministic fallback serves results within degraded SLO; response indicates limited explanation mode | P0 | SRE | Not Started |
| EC-P4-006 | P4 | Cost | Token budget alarms configured | High traffic + large candidate requests | 1) Run load test 2) Monitor token usage | Candidate cap and budget controls activate; cost remains within threshold without complete service failure | P1 | SRE/AI Platform | Not Started |

## Execution Cadence Recommendation
- **Per PR:** Run all impacted `P0` cases + one fallback test.
- **Nightly:** Run full P0/P1 regression suite including outage simulations.
- **Pre-release:** Run all phases with load, reliability, and cost controls enabled.
