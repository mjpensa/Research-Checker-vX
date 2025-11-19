# Phase 3: Advanced Features - Complete! 🎉

Phase 3 adds sophisticated analysis capabilities: dependency inference, contradiction detection, and comprehensive report generation.

## What's New in Phase 3

### 1. **Dependency Inference Engine** ✅
- Analyzes relationships between claims using Gemini 2.5 Flash
- Identifies 7 types of dependencies:
  - **CAUSAL**: One claim causes or enables another
  - **EVIDENTIAL**: One claim provides evidence for another
  - **TEMPORAL**: Claims have chronological relationships
  - **PREREQUISITE**: One claim requires another to be true
  - **CONTRADICTORY**: Claims conflict with each other
  - **REFINES**: One claim is a more specific version of another
  - **NONE**: No significant relationship
- Smart pair generation to optimize analysis
- Confidence scoring for each relationship

### 2. **Graph Analysis with NetworkX** ✅
- Builds directed graph of claim dependencies
- Calculates **PageRank** for claim importance
- Computes **betweenness centrality**
- Identifies **foundational claims**
  - High outgoing dependencies
  - Low incoming dependencies
  - Critical to the argument structure
- Combined **importance score** weighting PageRank and centrality

### 3. **Contradiction Detection** ✅
- Identifies conflicting claims across sources
- Categorizes contradictions:
  - **DIRECT**: Opposite factual statements
  - **NUMERICAL**: Different values for same metric
  - **TEMPORAL**: Conflicting dates/sequences
  - **SCOPE**: Universal vs particular conflicts
  - **DEFINITIONAL**: Different term meanings
- Severity ratings: low, medium, high, critical
- Resolution suggestions provided

### 4. **Report Generation** ✅
- Comprehensive synthesis reports with:
  - **Executive Summary**: High-level overview
  - **Consensus Findings**: Well-supported claims
  - **Key Insights**: Novel connections discovered
  - **Disputed Areas**: Contradictions and gaps
  - **Dependency Analysis**: Critical chains and vulnerabilities
  - **Recommendations**: Next research steps
- Markdown formatted for easy export
- Claim ID citations throughout
- Statistics and metrics included

### 5. **New API Endpoints** ✅

#### Reports
- `POST /api/v1/reports/{id}/analyze-dependencies` - Start dependency analysis
- `POST /api/v1/reports/{id}/detect-contradictions` - Find contradictions
- `POST /api/v1/reports/{id}/generate` - Generate synthesis report
- `GET /api/v1/reports/{id}` - List all reports
- `GET /api/v1/reports/{id}/latest` - Get most recent report
- `GET /api/v1/reports/report/{report_id}` - Get specific report
- `GET /api/v1/reports/{id}/contradictions` - List contradictions

## Quick Start

### 1. Start All Services

**Terminal 1 - API:**
```bash
cd apps/api
python main.py
```

**Terminal 2 - Claim Extraction Worker:**
```bash
cd apps/workers
python worker_extraction.py
```

**Terminal 3 - Dependency Inference Worker:**
```bash
cd apps/workers
python worker_inference.py
```

**Terminal 4 - Report Generation Worker:**
```bash
cd apps/workers
python worker_reports.py
```

### 2. Run Complete Test

```bash
# First run Phase 2 to get a pipeline with claims
cd apps/api
python test_phase2.py

# Note the pipeline ID from output, then run:
python test_phase3.py <pipeline-id>
```

## Complete Workflow Example

### Step 1: Create Pipeline & Upload Documents
```bash
curl -X POST http://localhost:8000/api/v1/pipelines/ \
  -H "Content-Type: application/json" \
  -d '{"name": "AI Research Analysis"}'

# Note the pipeline_id, then upload documents
curl -X POST http://localhost:8000/api/v1/pipelines/{pipeline_id}/documents \
  -F "files=@research1.pdf" \
  -F "files=@research2.pdf" \
  -F "source_llm=gpt-4"
```

### Step 2: Extract Claims
```bash
curl -X POST http://localhost:8000/api/v1/pipelines/{pipeline_id}/start
```
Wait for `worker_extraction.py` to process.

### Step 3: Analyze Dependencies
```bash
curl -X POST http://localhost:8000/api/v1/reports/{pipeline_id}/analyze-dependencies
```
Wait for `worker_inference.py` to complete (30-60 seconds per 10 claims).

### Step 4: Detect Contradictions
```bash
curl -X POST http://localhost:8000/api/v1/reports/{pipeline_id}/detect-contradictions
```

### Step 5: Generate Report
```bash
curl -X POST "http://localhost:8000/api/v1/reports/{pipeline_id}/generate?report_type=synthesis"
```
Wait for `worker_reports.py` to generate the report.

### Step 6: Retrieve Report
```bash
curl http://localhost:8000/api/v1/reports/{pipeline_id}/latest
```

## Architecture

```
┌─────────────┐
│   Claims    │
│  (Phase 2)  │
└──────┬──────┘
       │
       ▼
┌────────────────┐       ┌──────────────┐
│   Dependency   │──────▶│   Gemini     │
│    Inference   │       │  2.5 Flash   │
│     Worker     │◀──────│              │
└────────┬───────┘       └──────────────┘
         │
         ▼
┌────────────────┐
│   NetworkX     │
│ Graph Analysis │
│  - PageRank    │
│  - Centrality  │
│  - Foundational│
└────────┬───────┘
         │
         ▼
┌────────────────┐       ┌──────────────┐
│ Contradiction  │──────▶│   Gemini     │
│   Detection    │       │  2.5 Flash   │
└────────┬───────┘       └──────────────┘
         │
         ▼
┌────────────────┐       ┌──────────────┐
│     Report     │──────▶│   Gemini     │
│   Generation   │       │  2.5 Flash   │
│     Worker     │◀──────│              │
└────────────────┘       └──────────────┘
```

## Worker Details

### Dependency Inference Worker
**Location**: `apps/workers/worker_inference.py`

**What it does**:
1. Fetches all claims from pipeline
2. Generates smart claim pairs (prioritizing important claims)
3. For each pair, calls Gemini to determine relationship
4. Saves high-confidence dependencies (>0.7)
5. Builds NetworkX graph
6. Calculates PageRank and centrality
7. Identifies foundational claims
8. Updates claim importance scores

**Performance**:
- Analyzes ~15 pairs per batch
- Processes ~250 pairs max per pipeline
- Takes 2-4 seconds per pair
- Total time: ~30-60 seconds for 10 claims

### Report Generation Worker
**Location**: `apps/workers/worker_reports.py`

**What it does**:
1. Gathers all pipeline data (claims, dependencies, contradictions)
2. Formats data for report generation
3. Calls Gemini with comprehensive prompt
4. Extracts key findings and recommendations
5. Saves markdown report to database
6. Includes statistics and metrics

**Report Sections**:
- Executive Summary (2-3 paragraphs)
- Consensus Findings (well-supported claims)
- Key Insights (novel connections)
- Disputed Areas (contradictions)
- Dependency Analysis (critical chains)
- Recommendations (next steps)

## Performance Optimization

### Smart Pair Generation
Instead of analyzing all N² pairs, we use intelligent strategies:

1. **High-confidence claims**: Top 20% analyzed against all others
2. **Within-type pairs**: Same claim type often related
3. **Deduplication**: Remove duplicate pairs
4. **Limiting**: Cap at 250-300 pairs maximum

This reduces from O(N²) to O(N) complexity.

### Batch Processing
- Process 15 claim pairs per batch
- Commit after each batch
- Update progress incrementally
- Allow for graceful interruption

### Caching
- Gemini responses cached in Redis (24h TTL)
- Reduces redundant API calls
- Speeds up retries and re-analysis

## Graph Metrics Explained

### PageRank
- Measures claim importance in dependency network
- Higher PageRank = more central to argument
- Range: 0.0 to 1.0
- Foundational claims often have high PageRank

### Betweenness Centrality
- Measures how often claim appears on shortest paths
- High centrality = bridges different claim clusters
- Range: 0.0 to 1.0
- Critical connection points have high centrality

### Foundational Claims
Claims that:
- Have 3+ outgoing dependencies
- Have ≤2 incoming dependencies
- Form the base of argument structure
- Often represent core assumptions or findings

### Importance Score
Combined metric:
```
importance = (pagerank × 0.7) + (centrality × 0.3)
```

## Contradiction Types

### DIRECT
- One claim states X, another states not-X
- Example: "A increases B" vs "A decreases B"
- Severity: Usually high or critical

### NUMERICAL
- Different values for the same measurement
- Example: "95% success rate" vs "75% success rate"
- Severity: Medium to high

### TEMPORAL
- Conflicting dates or time sequences
- Example: "Before 2020" vs "After 2020"
- Severity: Low to medium

### SCOPE
- Universal claim conflicts with particular claim
- Example: "All X are Y" vs "Some X are not Y"
- Severity: Medium

### DEFINITIONAL
- Different meanings of same term
- Example: "AI means machine learning" vs "AI includes expert systems"
- Severity: Low to medium

## API Response Examples

### Dependency Example
```json
{
  "id": "dep-123",
  "source_claim_id": "claim-456",
  "target_claim_id": "claim-789",
  "relationship_type": "evidential",
  "confidence": 0.89,
  "strength": "strong",
  "explanation": "Claim A provides empirical evidence supporting Claim B",
  "semantic_markers": ["study", "found", "supports"]
}
```

### Contradiction Example
```json
{
  "id": "contra-123",
  "claim_a_id": "claim-111",
  "claim_b_id": "claim-222",
  "contradiction_type": "numerical",
  "severity": "high",
  "confidence": 0.92,
  "explanation": "Different accuracy values reported for the same model",
  "resolution_suggestion": "Verify which study used more rigorous methodology"
}
```

### Report Statistics Example
```json
{
  "total_claims": 45,
  "total_dependencies": 78,
  "total_contradictions": 3,
  "foundational_claims": 8,
  "documents_analyzed": 5
}
```

## Troubleshooting

### No dependencies found
1. Check worker_inference.py is running
2. Verify claims exist (`total_claims > 1`)
3. Check Gemini API key is valid
4. Look for errors in worker logs

### Contradictions not detected
1. May be no actual contradictions (good thing!)
2. Check claims have sufficient content
3. Verify Gemini API is responding
4. Review minimum confidence threshold (0.7)

### Report generation fails
1. Ensure dependencies were analyzed first
2. Check worker_reports.py is running
3. Verify sufficient claims exist (>5 recommended)
4. Check Gemini API quota/limits

## What's Next: Phase 4

Phase 4 will add the frontend:
- Next.js application
- Interactive dependency graph visualization
- Claims table with filtering and sorting
- Real-time WebSocket updates
- Report viewing and export
- User authentication with Clerk

## File Structure

```
apps/
├── api/
│   ├── routes/
│   │   └── reports/router.py          # Reports API routes ✨ NEW
│   ├── services/
│   │   └── contradiction_detector.py  # Contradiction service ✨ NEW
│   └── test_phase3.py                 # Phase 3 tests ✨ NEW
│
└── workers/
    ├── worker_inference.py            # Dependency worker ✨ NEW
    ├── worker_reports.py              # Report worker ✨ NEW
    └── requirements.txt               # Added NetworkX ✨ UPDATED
```

## Railway Deployment

Add these workers to `railway.toml`:

```toml
[services.worker-inference]
source = "./apps/workers"
buildCommand = "pip install -r requirements.txt"
startCommand = "python worker_inference.py"
replicas = 1

[services.worker-reports]
source = "./apps/workers"
buildCommand = "pip install -r requirements.txt"
startCommand = "python worker_reports.py"
replicas = 1
```

---

**Status**: Phase 3 Complete ✅
**Next**: Phase 4 - Frontend (Next.js, interactive graphs, user auth)
