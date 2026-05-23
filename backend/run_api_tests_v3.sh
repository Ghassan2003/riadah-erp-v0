#!/bin/bash
# Complete API test for Riadah ERP v0 - fixed auth header
set -o pipefail

cd /home/z/my-project/riadah-erp-v0/backend

# Kill old server
pkill -f "manage.py runserver" 2>/dev/null
sleep 1

# Start server
python manage.py runserver 0.0.0.0:8000 > /tmp/django_test2.log 2>&1 &
SERVER_PID=$!
sleep 10

# Verify server is up
CHECK=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8000/api/auth/login/ 2>/dev/null)
if [ "$CHECK" = "000" ]; then
    echo "SERVER_FAILED"
    cat /tmp/django_test2.log
    exit 1
fi
echo "SERVER_UP"

# Get auth token
TOKEN=$(curl -s --max-time 10 -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "TOKEN_FAILED"
else
    echo "TOKEN_OK:${TOKEN:0:30}"
fi

# Save token to file for curl to read
echo "Bearer $TOKEN" > /tmp/auth_token.txt

# Test function - use separate curl commands for auth vs no-auth
test_ep_noauth() {
    local label="$1" method="$2" url="$3" data="$4"
    local start end ms http_code tmpf
    start=$(date +%s%N)
    tmpf=$(mktemp)
    
    if [ -n "$data" ]; then
        http_code=$(curl -s -o "$tmpf" -w "%{http_code}" --max-time 8 \
            -X "$method" -H "Content-Type: application/json" \
            -d "$data" "http://localhost:8000$url" 2>/dev/null || echo "000")
    else
        http_code=$(curl -s -o "$tmpf" -w "%{http_code}" --max-time 8 \
            -X "$method" "http://localhost:8000$url" 2>/dev/null || echo "000")
    fi
    
    end=$(date +%s%N)
    ms=$(( (end - start) / 1000000 ))
    body=$(head -c 150 "$tmpf" 2>/dev/null | tr '\n' ' ')
    rm -f "$tmpf"
    
    printf "%s|%s|%s|%s|%s|%s\n" "$label" "$method" "$url" "$http_code" "${ms}ms" "$body"
}

test_ep_auth() {
    local label="$1" method="$2" url="$3" data="$4"
    local start end ms http_code tmpf
    start=$(date +%s%N)
    tmpf=$(mktemp)
    
    if [ -n "$data" ]; then
        http_code=$(curl -s -o "$tmpf" -w "%{http_code}" --max-time 8 \
            -X "$method" -H "Content-Type: application/json" \
            -H "Authorization: Bearer $TOKEN" \
            -d "$data" "http://localhost:8000$url" 2>/dev/null || echo "000")
    else
        http_code=$(curl -s -o "$tmpf" -w "%{http_code}" --max-time 8 \
            -X "$method" -H "Authorization: Bearer $TOKEN" \
            "http://localhost:8000$url" 2>/dev/null || echo "000")
    fi
    
    end=$(date +%s%N)
    ms=$(( (end - start) / 1000000 ))
    body=$(head -c 150 "$tmpf" 2>/dev/null | tr '\n' ' ')
    rm -f "$tmpf"
    
    printf "%s|%s|%s|%s|%s|%s\n" "$label" "$method" "$url" "$http_code" "${ms}ms" "$body"
}

echo ""
echo "=== SECTION 1: NO AUTH (should all be 401 except public endpoints) ==="
# --- Auth ---
test_ep_noauth "Auth Profile" GET "/api/auth/profile/" ""
test_ep_noauth "User List" GET "/api/auth/users/" ""
# --- Sales ---
test_ep_noauth "Sales Orders" GET "/api/sales/orders/" ""
test_ep_noauth "Sales Customers" GET "/api/sales/customers/" ""
test_ep_noauth "Sales Stats" GET "/api/sales/stats/" ""
# --- Projects ---
test_ep_noauth "Projects Stats" GET "/api/projects/stats/" ""
test_ep_noauth "Projects Phases" GET "/api/projects/phases/" ""
test_ep_noauth "Projects Risks" GET "/api/projects/risks/" ""
test_ep_noauth "Budget Items" GET "/api/projects/budget-items/" ""
test_ep_noauth "Time Entries" GET "/api/projects/time-entries/" ""
test_ep_noauth "Proj Contracts" GET "/api/projects/contracts/" ""
test_ep_noauth "Proj Documents" GET "/api/projects/documents/" ""
test_ep_noauth "Milestones" GET "/api/projects/milestones/" ""
test_ep_noauth "Budget Stats" GET "/api/projects/budget-stats/" ""
test_ep_noauth "Risk Matrix" GET "/api/projects/risk-matrix/" ""
test_ep_noauth "Time Report" GET "/api/projects/time-report/" ""
# --- CRM ---
test_ep_noauth "CRM Stats" GET "/api/crm/stats/" ""
test_ep_noauth "CRM Tickets" GET "/api/crm/tickets/" ""
test_ep_noauth "SLA Policies" GET "/api/crm/sla-policies/" ""
test_ep_noauth "Quotations" GET "/api/crm/quotations/" ""
test_ep_noauth "Commissions" GET "/api/crm/commissions/" ""
test_ep_noauth "Ticket Stats" GET "/api/crm/ticket-stats/" ""
test_ep_noauth "Commission Stats" GET "/api/crm/commission-stats/" ""
test_ep_noauth "Pipeline Funnel" GET "/api/crm/pipeline/funnel/" ""
test_ep_noauth "Sales Forecast" GET "/api/crm/sales-forecast/" ""
# --- POS ---
test_ep_noauth "POS Stats" GET "/api/pos/stats/" ""
test_ep_noauth "Price Lists" GET "/api/pos/price-lists/" ""
test_ep_noauth "Discount Rules" GET "/api/pos/discount-rules/" ""
test_ep_noauth "Promo Codes" GET "/api/pos/promo-codes/" ""
test_ep_noauth "Loyalty Programs" GET "/api/pos/loyalty-programs/" ""
test_ep_noauth "POS Tables" GET "/api/pos/tables/" ""
test_ep_noauth "POS Shifts" GET "/api/pos/shifts/" ""
test_ep_noauth "Installments" GET "/api/pos/installments/" ""
# --- Accounting ---
test_ep_noauth "Acct Accounts" GET "/api/accounting/accounts/" ""
test_ep_noauth "Acct Stats" GET "/api/accounting/stats/" ""
test_ep_noauth "Acct Entries" GET "/api/accounting/entries/" ""
# --- HR ---
test_ep_noauth "HR Employees" GET "/api/hr/employees/" ""
test_ep_noauth "HR Departments" GET "/api/hr/departments/" ""
test_ep_noauth "HR Stats" GET "/api/hr/stats/" ""
# --- Purchases ---
test_ep_noauth "Purchase Orders" GET "/api/purchases/orders/" ""
test_ep_noauth "Suppliers" GET "/api/purchases/suppliers/" ""
test_ep_noauth "Purchase Stats" GET "/api/purchases/stats/" ""
# --- Invoicing ---
test_ep_noauth "Invoices" GET "/api/invoicing/" ""
test_ep_noauth "Invoicing Stats" GET "/api/invoicing/stats/" ""
# --- Analytics ---
test_ep_noauth "Anomalies" GET "/api/analytics/anomalies/" ""
test_ep_noauth "Run Forecast" POST "/api/analytics/run-forecast/" "{}"
# --- Chatbot ---
test_ep_noauth "Chatbot Convos" GET "/api/chatbot/conversations/" ""
# --- Notifications ---
test_ep_noauth "Notifications" GET "/api/notifications/" ""
# --- Documents ---
test_ep_noauth "Documents" GET "/api/documents/" ""
# --- Payments ---
test_ep_noauth "Payment Txns" GET "/api/payments/transactions/" ""

echo ""
echo "=== SECTION 2: WITH AUTH (should be 200/201 for list views) ==="
# --- Auth ---
test_ep_auth "Auth Profile" GET "/api/auth/profile/" ""
test_ep_auth "User List" GET "/api/auth/users/" ""
# --- Sales ---
test_ep_auth "Sales Orders" GET "/api/sales/orders/" ""
test_ep_auth "Sales Customers" GET "/api/sales/customers/" ""
test_ep_auth "Sales Stats" GET "/api/sales/stats/" ""
# --- Projects ---
test_ep_auth "Projects Stats" GET "/api/projects/stats/" ""
test_ep_auth "Projects Phases" GET "/api/projects/phases/" ""
test_ep_auth "Projects Risks" GET "/api/projects/risks/" ""
test_ep_auth "Budget Items" GET "/api/projects/budget-items/" ""
test_ep_auth "Time Entries" GET "/api/projects/time-entries/" ""
test_ep_auth "Proj Contracts" GET "/api/projects/contracts/" ""
test_ep_auth "Proj Documents" GET "/api/projects/documents/" ""
test_ep_auth "Milestones" GET "/api/projects/milestones/" ""
test_ep_auth "Budget Stats" GET "/api/projects/budget-stats/" ""
test_ep_auth "Risk Matrix" GET "/api/projects/risk-matrix/" ""
test_ep_auth "Time Report" GET "/api/projects/time-report/" ""
# --- CRM ---
test_ep_auth "CRM Stats" GET "/api/crm/stats/" ""
test_ep_auth "CRM Tickets" GET "/api/crm/tickets/" ""
test_ep_auth "SLA Policies" GET "/api/crm/sla-policies/" ""
test_ep_auth "Quotations" GET "/api/crm/quotations/" ""
test_ep_auth "Commissions" GET "/api/crm/commissions/" ""
test_ep_auth "Ticket Stats" GET "/api/crm/ticket-stats/" ""
test_ep_auth "Commission Stats" GET "/api/crm/commission-stats/" ""
test_ep_auth "Pipeline Funnel" GET "/api/crm/pipeline/funnel/" ""
test_ep_auth "Sales Forecast" GET "/api/crm/sales-forecast/" ""
# --- POS ---
test_ep_auth "POS Stats" GET "/api/pos/stats/" ""
test_ep_auth "Price Lists" GET "/api/pos/price-lists/" ""
test_ep_auth "Discount Rules" GET "/api/pos/discount-rules/" ""
test_ep_auth "Promo Codes" GET "/api/pos/promo-codes/" ""
test_ep_auth "Loyalty Programs" GET "/api/pos/loyalty-programs/" ""
test_ep_auth "POS Tables" GET "/api/pos/tables/" ""
test_ep_auth "POS Shifts" GET "/api/pos/shifts/" ""
test_ep_auth "Installments" GET "/api/pos/installments/" ""
# --- Accounting ---
test_ep_auth "Acct Accounts" GET "/api/accounting/accounts/" ""
test_ep_auth "Acct Stats" GET "/api/accounting/stats/" ""
test_ep_auth "Acct Entries" GET "/api/accounting/entries/" ""
# --- HR ---
test_ep_auth "HR Employees" GET "/api/hr/employees/" ""
test_ep_auth "HR Departments" GET "/api/hr/departments/" ""
test_ep_auth "HR Stats" GET "/api/hr/stats/" ""
# --- Purchases ---
test_ep_auth "Purchase Orders" GET "/api/purchases/orders/" ""
test_ep_auth "Suppliers" GET "/api/purchases/suppliers/" ""
test_ep_auth "Purchase Stats" GET "/api/purchases/stats/" ""
# --- Invoicing ---
test_ep_auth "Invoices" GET "/api/invoicing/" ""
test_ep_auth "Invoicing Stats" GET "/api/invoicing/stats/" ""
# --- Analytics ---
test_ep_auth "Anomalies" GET "/api/analytics/anomalies/" ""
test_ep_auth "Run Forecast" POST "/api/analytics/run-forecast/" "{}"
# --- Chatbot ---
test_ep_auth "Chatbot Convos" GET "/api/chatbot/conversations/" ""
test_ep_auth "Chatbot Chat" POST "/api/chatbot/chat/" '{"message":"مرحبا"}'
# --- Notifications ---
test_ep_auth "Notifications" GET "/api/notifications/" ""
# --- Documents ---
test_ep_auth "Documents" GET "/api/documents/" ""
# --- Payments ---
test_ep_auth "Payment Txns" GET "/api/payments/transactions/" ""

echo ""
echo "=== SECTION 3: CRUD OPERATIONS ==="
test_ep_auth "Phase POST empty" POST "/api/projects/phases/" '{}'
test_ep_auth "Phase POST data" POST "/api/projects/phases/" '{"name":"Test Phase","project":1}'
test_ep_auth "Ticket POST empty" POST "/api/crm/tickets/" '{}'
test_ep_auth "Ticket POST data" POST "/api/crm/tickets/" '{"subject":"Test Ticket","priority":"medium"}'
test_ep_auth "PriceList POST empty" POST "/api/pos/price-lists/" '{}'
test_ep_auth "PriceList POST data" POST "/api/pos/price-lists/" '{"name":"Test Price List"}'
test_ep_auth "SalesOrder POST empty" POST "/api/sales/orders/create/" '{}'

echo ""
echo "=== SECTION 4: ERROR HANDLING ==="
test_ep_noauth "Nonexistent" GET "/api/nonexistent/" ""
test_ep_noauth "Invalid method" DELETE "/api/sales/orders/" ""
test_ep_noauth "Bad login" POST "/api/auth/login/" '{"username":"bad","password":"bad"}'
test_ep_auth "Invalid proj ID" GET "/api/projects/999999/" ""
test_ep_auth "Invalid user ID" GET "/api/auth/users/999999/" ""
# Test wrong task-specified endpoints (404 expected)
test_ep_noauth "WRONG /api/auth/me/" GET "/api/auth/me/" ""
test_ep_noauth "WRONG /api/users/users/" GET "/api/users/users/" ""
test_ep_noauth "WRONG /api/users/stats/" GET "/api/users/stats/" ""
test_ep_noauth "WRONG /api/invoicing/invoices/" GET "/api/invoicing/invoices/" ""
test_ep_noauth "WRONG /api/analytics/forecasting/" GET "/api/analytics/forecasting/" ""
test_ep_noauth "WRONG /api/documents/documents/" GET "/api/documents/documents/" ""
test_ep_noauth "WRONG /api/payments/payments/" GET "/api/payments/payments/" ""
test_ep_noauth "WRONG /api/crm/pipeline-funnel/" GET "/api/crm/pipeline-funnel/" ""

# Kill server
kill $SERVER_PID 2>/dev/null
echo ""
echo "DONE"
