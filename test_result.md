#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Build up the EUDI-Nexus platform with the PNIA (Production Network ID Architecture)
  concept, fully EU-compliant (EU AI Act, DSGVO/GDPR, DMA). Merge the advanced build
  (Säule B) from the user's backup and add a new Memorial & Honorary Registry
  (Gedenktafeln for deceased / Ehrenplätze for living) plus the Concil Protokoll (CP-01)
  core with CIH-01 handshake and the protected Urheberrecht/Register statement.

backend:
  - task: "PNIA Registry — public read endpoints (plaques, compliance, ai-audit)"
    implemented: true
    working: true
    file: "backend/routers/pnia_registry.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GET /api/pnia/registry/plaques (filter by type), /plaques/{id}, /compliance, /ai-audit, /ai-audit/verify, / (info). Seeded 16 memorials + 1 honorary = 17 plaques. Verify counts, filters, and public shape (no raw PII)."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (9/9). GET /api/pnia/registry/ returns service info with compliance keys. GET /plaques returns 17 plaques with correct structure (content_payload, ai_generated_content, risk_classification, NO raw PII leak). Filters work: ?type=MEMORIAL_BOARD returns 16, ?type=HONORARY_PLACE returns 1. GET /plaques/{id} retrieves individual plaque. GET /compliance returns correct counts (memorial_boards=16, honorary_places=1, pii_encryption=AES-256-GCM, audit_chain_valid=true). GET /ai-audit and /ai-audit/verify both working (valid=true)."
  - task: "PNIA Registry — protected write + AI (individuals, consents, plaques, generate-tribute, RTBF)"
    implemented: true
    working: true
    file: "backend/routers/pnia_registry.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Protected via Bearer (see test_credentials.md). Endpoints: POST /individuals (PII AES-256-GCM encrypted), POST /consents, POST /plaques (enforces consent for LIVING + type/status match), POST /plaques/{id}/generate-tribute (real gpt-5.4 via emergentintegrations, sets ai_generated_content + risk LIMITED_RISK_TRANSPARENCY + hash-chained AiAuditLog), POST /plaques/{id}/lock, POST /consents/{id}/revoke (DSGVO Art.17 crypto-shred + cascade). Verify 401 without Bearer. Generate-tribute costs LLM credits — test ONCE."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (11/11). Auth enforcement: POST /individuals and POST /plaques without Bearer correctly return 401. Full compliance flow verified: (1) Created LIVING individual with encrypted PII, (2) Attempt to create plaque without consent correctly returns 403 (DSGVO Art.6/7), (3) Created consent with status=GRANTED, (4) Created plaque with consent succeeds (is_active=true, ai_generated_content=false, risk=MINIMAL_RISK), (5) GET /individuals/{id} with Bearer returns decrypted PII (given_name=Maria), (6) POST /consents/{id}/revoke successfully crypto-shreds PII (revoked=true, erased=true, deactivated_plaques=1), (7) GET /individuals/{id} after revoke confirms erased=true and pii=null (DSGVO Art.17 verified), (8) Type/status mismatch (LIVING + MEMORIAL_BOARD) correctly returns 422. AI generation tested ONCE: generate-tribute returned German tribute text (348 chars), set ai_generated_content=true, risk=LIMITED_RISK_TRANSPARENCY, created audit hash, audit chain still valid. Lock plaque works, generate-tribute on locked plaque correctly returns 409."
  - task: "PNIA Concil (CP-01) — concept, CIH-01 handshake, ownership"
    implemented: true
    working: true
    file: "backend/routers/pnia_concil.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GET /api/pnia/concil/ (concept: 4 pillars, roles), /discovery (signed), /ownership (© Daniel Pohl register). POST /handshake: all 4 invariants + commitment => status 200 ESTABLISHED_ACCESS; missing invariant or commitment => status 403 GOVERNANCE_MISMATCH + sovereignty_shield=isolated."
        -working: false
        -agent: "testing"
        -comment: "❌ Handshake returned HTTP 200 even for governance mismatch (body.status=403 but HTTP layer 200). Router did not translate decision to HTTP status. GET endpoints all correct."
        -working: true
        -agent: "main"
        -comment: "FIXED: router returns JSONResponse(status_code=result['status']) → mismatch yields real HTTP 403 with decision envelope; frontend catch reads e.response.data. Verified via curl: valid=>HTTP200, missing invariant=>HTTP403 (GOVERNANCE_MISMATCH, shield isolated), missing commitment=>HTTP403."
  - task: "Säule B merge — pnia-compliance (BSI report) + identity-broker"
    implemented: true
    working: true
    file: "backend/routers/pnia_compliance.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GET /api/pnia-compliance/bsi-report + POST /check (subprocess eu_arf_compliance_check.py). GET /api/identity-broker/providers (23 providers) + /health. Merged 1:1 from user backup."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (4/4). GET /api/pnia-compliance/bsi-report returns status=PASS with 5 checks. GET /api/pnia-compliance/ returns service info (PNIA EU-ARF Compliance Validator). GET /api/identity-broker/providers returns 23 providers. GET /api/identity-broker/health returns status=healthy."

frontend:
  - task: "PNIA Registry page (/pnia-registry)"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/PNIARegistry.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Renders 17 plaques, compliance strip, filters, transparency (Art.50) badges, AI audit trail table. Screenshot verified rendering. Frontend testing pending user approval."
  - task: "PNIA Concept page (/pnia-concept)"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/PNIAConcept.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "CP-01 4 pillars, technical pillars, governance roles, live CIH-01 handshake demo, Urheberrecht/Register block. Screenshot verified rendering."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "PNIA Concil (CP-01) — concept, CIH-01 handshake, ownership"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: |
      Please test the NEW PNIA backend endpoints only. Use the Bearer token from
      /app/memory/test_credentials.md for protected endpoints. IMPORTANT: the
      generate-tribute endpoint uses a real LLM (gpt-5.4) — test it only ONCE to
      conserve credits. Focus: (1) public reads + correct counts (17 plaques),
      (2) 401 on protected without Bearer, (3) full compliance flow: create LIVING
      individual -> create plaque WITHOUT consent should 403 -> create consent ->
      create plaque succeeds; (4) DSGVO Art.17 revoke crypto-shreds PII (GET
      individual after revoke returns erased=true, pii=null) and deactivates plaques;
      (5) Concil handshake 200 vs 403 (Sovereignty Shield); (6) ownership + BSI report
      + identity-broker providers. Do NOT test existing EUDI-Nexus endpoints.
    -agent: "testing"
    -message: |
      BACKEND TESTING COMPLETE. Test results: 32/34 tests passed (94% success rate).
      
      ✅ WORKING (3/4 tasks):
      1. PNIA Registry public endpoints - All 9 tests passed
      2. PNIA Registry protected/AI endpoints - All 11 tests passed (including full DSGVO compliance flow and AI generation)
      3. Säule B merge (compliance + identity-broker) - All 4 tests passed
      
      ❌ CRITICAL ISSUE (1/4 tasks):
      PNIA Concil handshake validation - The service layer correctly validates invariants and returns
      {status:403} for governance mismatches, but the FastAPI router does not translate this to an
      HTTP 403 response. Currently returns HTTP 200 with body containing status:403.
      
      FIX REQUIRED in /app/backend/routers/pnia_concil.py (line 40-52):
      The post_handshake endpoint must check the result['status'] field and raise
      HTTPException(result['status'], detail=result) when status != 200.
      
      Example fix:
      ```python
      @router.post("/handshake")
      async def post_handshake(body: HandshakeRequest, request: Request) -> dict[str, Any]:
          actor = "anonymous"
          auth = request.headers.get("authorization", "")
          if auth:
              actor = "bearer-client"
          result = await concil.handshake(
              system_id=body.system_id,
              accepted_invariants=body.accepted_invariants,
              commitment=body.commitment,
              mode=body.mode,
              actor=actor,
          )
          if result.get("status") != 200:
              raise HTTPException(status_code=result["status"], detail=result)
          return result
      ```
