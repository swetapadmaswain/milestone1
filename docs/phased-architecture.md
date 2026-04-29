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
Harden system for real-world usage with production-grade API, monitoring, and cost controls.
### Components
- **API Gateway + Auth**
  - FastAPI-based REST API with request validation
  - Optional API key enforcement via `PHASE4_API_KEY`
  - Per-client rate limiting (default: 120 req/min)
  - Request/response logging and middleware
- **Caching Layer**
  - In-memory TTL cache for recommendation responses (default: 120s)
  - Cache hit/miss metrics and performance tracking
  - Configurable cache invalidation strategies
- **Monitoring and Observability**
  - Endpoint latency tracking with percentile metrics
  - Error/fallback counters and health checks
  - Groq token usage counters (`prompt_tokens`, `completion_tokens`)
  - `/metrics` endpoint exposing real-time system metrics
- **Quality/Safety Guardrails**
  - Input sanitization for prompt-injection prevention
  - LLM output validation against known candidate names
  - Deterministic fallback explanations on LLM failure
  - Content filtering and safety checks
- **LLM Service Integration**
  - Groq Chat Completions API integration (`llama-3.1-8b-instant`)
  - Configurable model selection via `GROQ_MODEL`
  - Timeout controls (default: 8s) and retry logic
  - Prompt version tracking (`v1-groq-phase4`)
- **CI/CD + Model/Prompt Versioning**
  - Reproducible deployments with version tracking
  - Environment-based configuration management
  - Rollback capabilities for prompt/model regressions
### Implementation Details
- **Backend Framework**: FastAPI with Pydantic models for request/response validation
- **Data Storage**: Parquet files for restaurant catalog, JSON logs for feedback/metrics
- **LLM Integration**: Groq API with structured JSON response format
- **Caching**: In-memory dictionary-based cache with TTL
- **Monitoring**: Custom metrics service with counters and timers
- **Experimentation**: A/B testing framework with variant assignments
### Output
- Production-ready recommendation API with comprehensive monitoring
- Stable, observable, cost-controlled recommendation platform
- Real-time metrics and health endpoints
### Success Criteria
- SLOs met (availability, latency <2s)
- Controlled inference costs with no major quality regression
- Comprehensive monitoring and alerting coverage
- Zero-downtime deployments and rollback capability
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
## Backend Architecture
### Core Services
- **FastAPI Application Server**
  - RESTful API endpoints with OpenAPI documentation
  - Pydantic models for request/response validation
  - Middleware for timing, logging, and error handling
  - Automatic API documentation at `/docs`
- **Data Pipeline Service**
  - Dataset ingestion from Hugging Face
  - Data cleaning, normalization, and validation
  - Parquet/CSV storage for restaurant catalog
  - Schema validation and quality metrics
- **Recommendation Engine**
  - Rule-based filtering and scoring
  - LLM integration with Groq API
  - Personalization and experimentation logic
  - Hybrid ranking with configurable weights
- **Personalization Service**
  - User profile management (session + persistent)
  - Feedback capture and processing
  - Preference learning and decay
  - Time-based profile updates
- **Monitoring & Metrics Service**
  - Real-time metrics collection
  - Performance tracking (latency, throughput)
  - Error rates and fallback monitoring
  - Token usage and cost tracking
- **Cache Service**
  - In-memory TTL-based caching
  - Query result caching
  - Cache hit/miss tracking
  - Configurable eviction policies
- **Experimentation Service**
  - A/B testing framework
  - Variant assignment and tracking
  - Performance comparison metrics
  - Rollback capabilities

### API Endpoints
- **Health & Monitoring**
  - `GET /health` - Service health check
  - `GET /metrics` - Real-time system metrics
- **Data Management**
  - `POST /ingest` - Dataset ingestion and preparation
- **Recommendations**
  - `POST /recommend` - Get personalized recommendations
- **Feedback & Personalization**
  - `POST /feedback` - Capture user feedback
  - `GET /profile/{session_id}` - Get user profile summary

### Data Storage Architecture
- **Restaurant Catalog**
  - Primary storage: Parquet files (optimized for read operations)
  - Backup: CSV format for compatibility
  - Location: `storage/prepared/restaurants.parquet`
- **User Profiles**
  - JSON-based storage per user/session
  - Location: `storage/profiles/`
- **Feedback Logs**
  - Append-only JSONL format
  - Location: `storage/feedback/events.jsonl`
- **Experiment Assignments**
  - JSON configuration for A/B tests
  - Location: `storage/experiments/assignments.json`

### Security & Authentication
- **API Key Management**
  - Optional API key enforcement
  - Environment-based configuration
  - Per-client rate limiting
- **Input Validation**
  - Pydantic model validation
  - SQL injection prevention
  - Prompt injection sanitization
- **Output Filtering**
  - Content safety checks
  - PII protection
  - Structured response validation

## Frontend Architecture
### Web Application Structure
- **Modern React Application**
  - Component-based architecture
  - State management with Redux/Zustand
  - Responsive design with Tailwind CSS
  - Progressive Web App (PWA) capabilities
- **User Interface Components**
  - Search and filter controls
  - Restaurant recommendation cards
  - Interactive feedback mechanisms
  - Real-time metrics dashboard
- **User Experience Flow**
  1. **Landing Page** - System overview and quick search
  2. **Preference Input** - Location, budget, cuisine, rating preferences
  3. **Recommendation Results** - Ranked restaurant list with explanations
  4. **Detail View** - Individual restaurant information and feedback
  5. **Profile Dashboard** - User preferences and history

### Component Architecture
- **Search Components**
  - Location autocomplete with geocoding
  - Budget slider with visual indicators
  - Cuisine multi-select with search
  - Rating filter with star display
- **Recommendation Components**
  - Restaurant cards with key information
  - Explanation panels with AI insights
  - Confidence indicators and scoring breakdowns
  - Comparison tools for multiple restaurants
- **Feedback Components**
  - Like/dislike buttons with animations
  - Detailed rating forms
  - Implicit behavior tracking
  - Preference learning indicators

### State Management
- **Global State**
  - User preferences and filters
  - Recommendation results and pagination
  - User session and authentication
  - Application settings and configuration
- **Component State**
  - Form inputs and validation
  - UI interaction states
  - Local component data
  - Temporary UI states

### API Integration
- **Service Layer**
  - HTTP client with interceptors
  - Request/response transformation
  - Error handling and retry logic
  - Caching strategies
- **Real-time Features**
  - WebSocket connections for live updates
  - Server-sent events for notifications
  - Optimistic updates for better UX
  - Conflict resolution strategies

### Performance Optimization
- **Code Splitting**
  - Route-based lazy loading
  - Component-level splitting
  - Dynamic imports for features
  - Bundle size optimization
- **Caching Strategy**
  - Browser cache management
  - Service worker for offline support
  - API response caching
  - Image and asset optimization
- **Rendering Optimization**
  - Virtual scrolling for large lists
  - Memoization of expensive operations
  - Debounced search inputs
  - Efficient re-rendering patterns

### Mobile Responsiveness
- **Responsive Design**
  - Mobile-first approach
  - Touch-friendly interfaces
  - Adaptive layouts
  - Device-specific optimizations
- **Progressive Enhancement**
  - Core functionality without JavaScript
  - Enhanced features with modern browsers
  - Graceful degradation strategies
  - Accessibility compliance

## Deployment Architecture
### Container Strategy
- **Backend Services**
  - Docker containers for microservices
  - Multi-stage builds for optimization
  - Environment-specific configurations
  - Health check endpoints
- **Frontend Application**
  - Nginx serving static assets
  - Containerized build process
  - CDN integration for global distribution
  - Asset optimization and compression

### Infrastructure Components
- **Load Balancing**
  - Application load balancer
  - SSL termination
  - Health monitoring
  - Auto-scaling integration
- **Database Layer**
  - Primary data storage (Parquet files)
  - Backup and replication strategies
  - Connection pooling
  - Query optimization
- **Monitoring Stack**
  - Prometheus for metrics collection
  - Grafana for visualization
  - Alert management
  - Log aggregation and analysis

### CI/CD Pipeline
- **Continuous Integration**
  - Automated testing framework
  - Code quality checks
  - Security scanning
  - Build and artifact management
- **Continuous Deployment**
  - Blue-green deployments
  - Canary releases
  - Automated rollback
  - Environment promotion

### Environment Management
- **Development Environment**
  - Local development setup
  - Hot reload capabilities
  - Debug configurations
  - Mock services for testing
- **Staging Environment**
  - Production-like setup
  - Integration testing
  - Performance testing
  - User acceptance testing
- **Production Environment**
  - High availability setup
  - Disaster recovery
  - Monitoring and alerting
  - Security hardening

## Suggested Tech Stack (Updated)
- **Backend Framework**: FastAPI with Pydantic
- **Frontend Framework**: React 18+ with TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand or Redux Toolkit
- **Data Storage**: Parquet files + PostgreSQL for persistence
- **LLM Integration**: Groq API with structured responses
- **Caching**: Redis for distributed caching
- **Monitoring**: Prometheus + Grafana
- **Deployment**: Docker + Kubernetes
- **CI/CD**: GitHub Actions or GitLab CI
- **CDN**: Cloudflare or AWS CloudFront

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
