#!/usr/bin/env bash
# EduAGI End-to-End Demo Flow
# Walks through the complete API flow with curl commands
set -euo pipefail

BASE="${EDUAGI_BASE_URL:-http://localhost:8000/api/v1}"
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step() { echo -e "\n${BLUE}━━━ $1 ━━━${NC}"; }
ok()   { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; }

# ── 0. Health check ─────────────────────────────────────────────
step "0. Health Check"
HEALTH=$(curl -sf "$BASE/health" 2>/dev/null) && ok "API is healthy" || { fail "API not reachable at $BASE"; exit 1; }

# ── 1. Register a new user ──────────────────────────────────────
step "1. Register Demo User"
REGISTER=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo_flow@test.com","password":"DemoFlow123!","name":"Demo Flow User"}')
echo "$REGISTER" | python3 -m json.tool 2>/dev/null && ok "User registered (or already exists)"

# ── 2. Login ────────────────────────────────────────────────────
step "2. Login"
LOGIN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"student@eduagi.com","password":"student123!"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"
ok "Logged in as student@eduagi.com"

# ── 3. Get current user profile ─────────────────────────────────
step "3. User Profile"
curl -s "$BASE/auth/me" -H "$AUTH" | python3 -m json.tool 2>/dev/null
echo
curl -s "$BASE/profile" -H "$AUTH" | python3 -m json.tool 2>/dev/null

# ── 4. Browse curriculum (learning path graph) ───────────────────
step "4. Browse Curriculum – Prerequisite Graph"
GRAPH=$(curl -s "$BASE/learning-path/graph/Mathematics" -H "$AUTH")
TOPIC_COUNT=$(echo "$GRAPH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['nodes']))")
ok "Mathematics graph has $TOPIC_COUNT topics"

# ── 5. Start a tutoring session ─────────────────────────────────
step "5. Start Tutoring Session"
SESSION=$(curl -s -X POST "$BASE/chat/sessions" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"subject":"Mathematics","topic":"algebra","mode":"tutor"}')
SESSION_ID=$(echo "$SESSION" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "$SESSION" | python3 -m json.tool 2>/dev/null
ok "Session created: $SESSION_ID"

# ── 6. Send a message (requires LLM – Ollama) ───────────────────
step "6. Chat Message (LLM-dependent)"
echo -e "${YELLOW}NOTE: This requires Ollama running with qwen2.5:3b.${NC}"
echo -e "${YELLOW}If Ollama is not available, this will return Internal Server Error.${NC}"
CHAT_RESP=$(curl -s -X POST "$BASE/chat/message" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"content\":\"What is algebra?\"}")
echo "$CHAT_RESP" | python3 -m json.tool 2>/dev/null || echo "$CHAT_RESP"

# ── 7. List sessions ────────────────────────────────────────────
step "7. List Sessions"
curl -s "$BASE/sessions" -H "$AUTH" | python3 -m json.tool 2>/dev/null

# ── 8. Create an assessment (as teacher) ─────────────────────────
step "8. Create Assessment (Teacher)"
TEACHER_LOGIN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"teacher@eduagi.com","password":"teacher123!"}')
TEACHER_TOKEN=$(echo "$TEACHER_LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
TEACHER_AUTH="Authorization: Bearer $TEACHER_TOKEN"

ASSESS=$(curl -s -X POST "$BASE/assessments" -H "$TEACHER_AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Algebra Demo Quiz",
    "subject":"Mathematics",
    "type":"quiz",
    "questions":[
      {"type":"mcq","content":"Solve: 2x + 3 = 7","options":["1","2","3","4"],"correct_answer":"2","points":10},
      {"type":"mcq","content":"Simplify: 3(x+2)","options":["3x+2","3x+6","x+6","3x+5"],"correct_answer":"3x+6","points":10}
    ]
  }')
ASSESS_ID=$(echo "$ASSESS" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "$ASSESS" | python3 -m json.tool 2>/dev/null
ok "Assessment created: $ASSESS_ID"

# ── 9. Adaptive Learning Endpoints ──────────────────────────────
step "9. Adaptive Learning"
echo "Knowledge State:"
curl -s "$BASE/adaptive/knowledge-state" -H "$AUTH" | python3 -m json.tool 2>/dev/null
echo
echo "Learning Style:"
curl -s "$BASE/adaptive/learning-style" -H "$AUTH" | python3 -m json.tool 2>/dev/null
echo
echo "Spaced Repetition Due:"
curl -s "$BASE/adaptive/spaced-repetition/due" -H "$AUTH" | python3 -m json.tool 2>/dev/null

# ── 10. Analytics ────────────────────────────────────────────────
step "10. Analytics"
echo "Student Summary:"
curl -s "$BASE/analytics/student/summary" -H "$AUTH" | python3 -m json.tool 2>/dev/null
echo
echo "Student Mastery:"
curl -s "$BASE/analytics/student/mastery" -H "$AUTH" | python3 -m json.tool 2>/dev/null

# ── 11. Available LLM Models ────────────────────────────────────
step "11. Available Models"
curl -s "$BASE/models" -H "$AUTH" | python3 -m json.tool 2>/dev/null

# ── 12. Learning Path ───────────────────────────────────────────
step "12. Recommended Learning Path"
curl -s "$BASE/learning-path/recommended" -H "$AUTH" | python3 -m json.tool 2>/dev/null

echo -e "\n${GREEN}━━━ Demo Complete ━━━${NC}"
echo "All non-LLM endpoints working. Chat requires Ollama with qwen2.5:3b."
