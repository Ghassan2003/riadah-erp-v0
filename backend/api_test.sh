#!/bin/bash
# Comprehensive API endpoint test script

BASE_URL="http://localhost:8000"
RESULTS_FILE="/tmp/api_test_results.txt"

# Clear previous results
> "$RESULTS_FILE"

echo "=========================================="
echo " Riadah ERP v0 - API Endpoint Test Suite"
echo "=========================================="
echo ""

# Function: test an endpoint
test_endpoint() {
    local method="$1"
    local url="$2"
    local auth="$3"
    local data="$4"
    local label="$5"
    
    local start_time=$(date +%s%N)
    local http_code
    local response
    
    if [ -n "$data" ]; then
        response=$(curl -s -o /tmp/api_response_body.txt -w "%{http_code}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            $([ -n "$auth" ] && echo "-H \"Authorization: Bearer $auth\"" || echo "") \
            -d "$data" \
            "$BASE_URL$url" \
            --max-time 10 2>/dev/null)
    else
        response=$(curl -s -o /tmp/api_response_body.txt -w "%{http_code}" \
            -X "$method" \
            $([ -n "$auth" ] && echo "-H \"Authorization: Bearer $auth\"" || echo "") \
            "$BASE_URL$url" \
            --max-time 10 2>/dev/null)
    fi
    
    local end_time=$(date +%s%N)
    local elapsed=$(( (end_time - start_time) / 1000000 ))
    
    # Truncate response body for display
    local body=$(head -c 200 /tmp/api_response_body.txt 2>/dev/null)
    
    if [ "$response" = "000" ]; then
        echo "| $label | $method | TIMEOUT/CONN_ERR | - | ${elapsed}ms | Connection failed |" >> "$RESULTS_FILE"
        echo "  FAIL: $label $method$url - TIMEOUT/CONN_ERR (${elapsed}ms)"
    else
        echo "| $label | $method | $response | $([ -n "$auth" ] && echo "Yes" || echo "No") | ${elapsed}ms | ${body:0:80} |" >> "$RESULTS_FILE"
        if [ "$response" -ge 500 ] 2>/dev/null; then
            echo "  FAIL: $label $method$url - HTTP $response (${elapsed}ms) - $body"
        else
            echo "  OK:   $label $method$url - HTTP $response (${elapsed}ms)"
        fi
    fi
}

# ========================================
# Step 1: Get Auth Token
# ========================================
echo "=== Getting Auth Token ==="
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login/" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' \
    --max-time 10 2>/dev/null)

TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "WARNING: Could not extract access token. Response was:"
    echo "$TOKEN_RESPONSE"
    echo "Will test without auth token for 'with auth' tests too."
    echo ""
fi

echo "Token obtained: ${TOKEN:0:30}..."
echo ""

# ========================================
# Step 2: Test endpoints WITHOUT auth
# ========================================
echo "=== Testing endpoints WITHOUT auth ==="
echo ""

NO_AUTH_ENDPOINTS=(
    "GET:/api/auth/me/:Auth - Me"
    "GET:/api/users/users/:Users List"
    "GET:/api/users/stats/:Users Stats"
    "GET:/api/sales/orders/:Sales Orders"
    "GET:/api/sales/customers/:Sales Customers"
    "GET:/api/sales/stats/:Sales Stats"
    "GET:/api/projects/stats/:Projects Stats"
    "GET:/api/projects/phases/:Projects Phases"
    "GET:/api/projects/risks/:Projects Risks"
    "GET:/api/projects/budget-items/:Budget Items"
    "GET:/api/projects/time-entries/:Time Entries"
    "GET:/api/projects/contracts/:Projects Contracts"
    "GET:/api/projects/documents/:Project Documents"
    "GET:/api/projects/milestones/:Milestones"
    "GET:/api/projects/budget-stats/:Budget Stats"
    "GET:/api/projects/risk-matrix/:Risk Matrix"
    "GET:/api/projects/time-report/:Time Report"
    "GET:/api/crm/stats/:CRM Stats"
    "GET:/api/crm/tickets/:CRM Tickets"
    "GET:/api/crm/sla-policies/:SLA Policies"
    "GET:/api/crm/quotations/:Quotations"
    "GET:/api/crm/commissions/:Commissions"
    "GET:/api/crm/ticket-stats/:Ticket Stats"
    "GET:/api/crm/commission-stats/:Commission Stats"
    "GET:/api/crm/pipeline-funnel/:Pipeline Funnel"
    "GET:/api/crm/sales-forecast/:Sales Forecast"
    "GET:/api/pos/stats/:POS Stats"
    "GET:/api/pos/price-lists/:Price Lists"
    "GET:/api/pos/discount-rules/:Discount Rules"
    "GET:/api/pos/promo-codes/:Promo Codes"
    "GET:/api/pos/loyalty-programs/:Loyalty Programs"
    "GET:/api/pos/tables/:POS Tables"
    "GET:/api/pos/shifts/:POS Shifts"
    "GET:/api/pos/installments/:Installments"
    "GET:/api/accounting/accounts/:Accounting Accounts"
    "GET:/api/accounting/stats/:Accounting Stats"
    "GET:/api/accounting/entries/:Accounting Entries"
    "GET:/api/hr/employees/:HR Employees"
    "GET:/api/hr/departments/:HR Departments"
    "GET:/api/hr/stats/:HR Stats"
    "GET:/api/purchases/orders/:Purchase Orders"
    "GET:/api/purchases/suppliers/:Suppliers"
    "GET:/api/purchases/stats/:Purchase Stats"
    "GET:/api/invoicing/invoices/:Invoices"
    "GET:/api/invoicing/stats/:Invoicing Stats"
    "GET:/api/analytics/forecasting/:Analytics Forecasting"
    "GET:/api/analytics/anomalies/:Analytics Anomalies"
    "GET:/api/chatbot/conversations/:Chatbot Conversations"
    "GET:/api/notifications/:Notifications"
    "GET:/api/documents/documents/:Documents"
    "GET:/api/assets/assets/:Assets"
    "GET:/api/assets/stats/:Assets Stats"
    "GET:/api/contracts/contracts/:Contracts"
    "GET:/api/payments/payments/:Payments"
)

for entry in "${NO_AUTH_ENDPOINTS[@]}"; do
    IFS=':' read -r METHOD URL LABEL <<< "$entry"
    test_endpoint "$METHOD" "$URL" "" "" "$LABEL"
done

echo ""

# ========================================
# Step 3: Test endpoints WITH auth
# ========================================
echo "=== Testing endpoints WITH auth ==="
echo ""

AUTH_ENDPOINTS=(
    "GET:/api/auth/me/:Auth - Me"
    "GET:/api/users/users/:Users List"
    "GET:/api/users/stats/:Users Stats"
    "GET:/api/sales/orders/:Sales Orders"
    "GET:/api/sales/customers/:Sales Customers"
    "GET:/api/sales/stats/:Sales Stats"
    "GET:/api/projects/stats/:Projects Stats"
    "GET:/api/projects/phases/:Projects Phases"
    "GET:/api/projects/risks/:Projects Risks"
    "GET:/api/projects/budget-items/:Budget Items"
    "GET:/api/projects/time-entries/:Time Entries"
    "GET:/api/projects/contracts/:Projects Contracts"
    "GET:/api/projects/documents/:Project Documents"
    "GET:/api/projects/milestones/:Milestones"
    "GET:/api/projects/budget-stats/:Budget Stats"
    "GET:/api/projects/risk-matrix/:Risk Matrix"
    "GET:/api/projects/time-report/:Time Report"
    "GET:/api/crm/stats/:CRM Stats"
    "GET:/api/crm/tickets/:CRM Tickets"
    "GET:/api/crm/sla-policies/:SLA Policies"
    "GET:/api/crm/quotations/:Quotations"
    "GET:/api/crm/commissions/:Commissions"
    "GET:/api/crm/ticket-stats/:Ticket Stats"
    "GET:/api/crm/commission-stats/:Commission Stats"
    "GET:/api/crm/pipeline-funnel/:Pipeline Funnel"
    "GET:/api/crm/sales-forecast/:Sales Forecast"
    "GET:/api/pos/stats/:POS Stats"
    "GET:/api/pos/price-lists/:Price Lists"
    "GET:/api/pos/discount-rules/:Discount Rules"
    "GET:/api/pos/promo-codes/:Promo Codes"
    "GET:/api/pos/loyalty-programs/:Loyalty Programs"
    "GET:/api/pos/tables/:POS Tables"
    "GET:/api/pos/shifts/:POS Shifts"
    "GET:/api/pos/installments/:Installments"
    "GET:/api/accounting/accounts/:Accounting Accounts"
    "GET:/api/accounting/stats/:Accounting Stats"
    "GET:/api/accounting/entries/:Accounting Entries"
    "GET:/api/hr/employees/:HR Employees"
    "GET:/api/hr/departments/:HR Departments"
    "GET:/api/hr/stats/:HR Stats"
    "GET:/api/purchases/orders/:Purchase Orders"
    "GET:/api/purchases/suppliers/:Suppliers"
    "GET:/api/purchases/stats/:Purchase Stats"
    "GET:/api/invoicing/invoices/:Invoices"
    "GET:/api/invoicing/stats/:Invoicing Stats"
    "GET:/api/analytics/forecasting/:Analytics Forecasting"
    "GET:/api/analytics/anomalies/:Analytics Anomalies"
    "GET:/api/chatbot/conversations/:Chatbot Conversations"
    "GET:/api/notifications/:Notifications"
    "GET:/api/documents/documents/:Documents"
    "GET:/api/assets/assets/:Assets"
    "GET:/api/assets/stats/:Assets Stats"
    "GET:/api/contracts/contracts/:Contracts"
    "GET:/api/payments/payments/:Payments"
)

for entry in "${AUTH_ENDPOINTS[@]}"; do
    IFS=':' read -r METHOD URL LABEL <<< "$entry"
    test_endpoint "$METHOD" "$URL" "$TOKEN" "" "$LABEL"
done

echo ""

# ========================================
# Step 4: CRUD Tests
# ========================================
echo "=== CRUD Tests ==="
echo ""

# POST chatbot message
test_endpoint "POST" "/api/chatbot/chat/" "$TOKEN" '{"message":"مرحبا"}' "Chatbot POST"

# POST project phase (empty data)
test_endpoint "POST" "/api/projects/phases/" "$TOKEN" '{}' "Phase POST empty"

# POST project phase (with data)
test_endpoint "POST" "/api/projects/phases/" "$TOKEN" '{"name":"Test Phase","project":1}' "Phase POST with data"

# POST ticket (empty data)
test_endpoint "POST" "/api/crm/tickets/" "$TOKEN" '{}' "Ticket POST empty"

# POST ticket (with data)
test_endpoint "POST" "/api/crm/tickets/" "$TOKEN" '{"subject":"Test Ticket","priority":"medium"}' "Ticket POST with data"

# POST price list (empty data)
test_endpoint "POST" "/api/pos/price-lists/" "$TOKEN" '{}' "PriceList POST empty"

# POST price list (with data)
test_endpoint "POST" "/api/pos/price-lists/" "$TOKEN" '{"name":"Test Price List"}' "PriceList POST with data"

echo ""

# ========================================
# Step 5: Error Handling Tests
# ========================================
echo "=== Error Handling Tests ==="
echo ""

test_endpoint "GET" "/api/nonexistent/" "" "" "Nonexistent endpoint"
test_endpoint "DELETE" "/api/sales/orders/" "" "" "Invalid method DELETE"
test_endpoint "POST" "/api/projects/phases/" "" '{}' "POST without auth"
test_endpoint "GET" "/api/projects/999999/" "$TOKEN" "" "Invalid project ID"
test_endpoint "GET" "/api/users/999999/" "$TOKEN" "" "Invalid user ID"
test_endpoint "POST" "/api/auth/login/" "" '{"username":"bad","password":"bad"}' "Login bad credentials"

echo ""

# ========================================
# Print summary table
# ========================================
echo "=========================================="
echo " RESULTS TABLE"
echo "=========================================="
echo "| Endpoint | Method | HTTP Status | Auth | Time | Notes |"
echo "|----------|--------|-------------|------|------|-------|"
cat "$RESULTS_FILE"
echo ""

# Count results
TOTAL=$(wc -l < "$RESULTS_FILE")
FAILS=$(grep -c "FAIL\|5[0-9][0-9]" "$RESULTS_FILE" 2>/dev/null || echo 0)
echo "Total tests: $TOTAL"
echo "Failures/Errors: $FAILS"
echo ""

echo "=========================================="
echo " DONE"
echo "=========================================="
