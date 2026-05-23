#!/bin/bash
# Complete API test for Riadah ERP v0 - all endpoints tested
set -o pipefail

cd /home/z/my-project/riadah-erp-v0/backend

# Kill old server
pkill -f "manage.py runserver" 2>/dev/null
sleep 1

# Start server
python manage.py runserver 0.0.0.0:8000 > /tmp/django_test.log 2>&1 &
SERVER_PID=$!
sleep 10

# Verify server is up
CHECK=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8000/api/auth/login/ 2>/dev/null)
if [ "$CHECK" = "000" ]; then
    echo "SERVER_FAILED"
    cat /tmp/django_test.log
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

# Test function - outputs: LABEL|METHOD|URL|HTTP_CODE|TIME_MS|RESPONSE_SNIPPET
test_ep() {
    local label="$1" method="$2" url="$3" use_auth="$4" data="$5"
    local start end ms http_code body
    start=$(date +%s%N)
    
    local tmpf=$(mktemp)
    local auth_header=""
    if [ "$use_auth" = "1" ] && [ -n "$TOKEN" ]; then
        auth_header="-H Authorization:\ Bearer\ $TOKEN"
    fi
    
    if [ -n "$data" ]; then
        http_code=$(curl -s -o "$tmpf" -w "%{http_code}" --max-time 8 \
            -X "$method" -H "Content-Type: application/json" \
            $auth_header -d "$data" "http://localhost:8000$url" 2>/dev/null || echo "000")
    else
        http_code=$(curl -s -o "$tmpf" -w "%{http_code}" --max-time 8 \
            -X "$method" $auth_header "http://localhost:8000$url" 2>/dev/null || echo "000")
    fi
    
    end=$(date +%s%N)
    ms=$(( (end - start) / 1000000 ))
    body=$(head -c 150 "$tmpf" 2>/dev/null | tr '\n' ' ')
    rm -f "$tmpf"
    
    printf "%s|%s|%s|%s|%s|%s\n" "$label" "$method" "$url" "$http_code" "${ms}ms" "$body"
}

echo "=== SECTION: NO AUTH ==="
# --- Auth ---
test_ep "Auth Profile" GET "/api/auth/profile/" 0 ""
test_ep "User List" GET "/api/auth/users/" 0 ""
# --- Sales ---
test_ep "Sales Orders" GET "/api/sales/orders/" 0 ""
test_ep "Sales Customers" GET "/api/sales/customers/" 0 ""
test_ep "Sales Stats" GET "/api/sales/stats/" 0 ""
# --- Projects ---
test_ep "Projects Stats" GET "/api/projects/stats/" 0 ""
test_ep "Projects Phases" GET "/api/projects/phases/" 0 ""
test_ep "Projects Risks" GET "/api/projects/risks/" 0 ""
test_ep "Budget Items" GET "/api/projects/budget-items/" 0 ""
test_ep "Time Entries" GET "/api/projects/time-entries/" 0 ""
test_ep "Proj Contracts" GET "/api/projects/contracts/" 0 ""
test_ep "Proj Documents" GET "/api/projects/documents/" 0 ""
test_ep "Milestones" GET "/api/projects/milestones/" 0 ""
test_ep "Budget Stats" GET "/api/projects/budget-stats/" 0 ""
test_ep "Risk Matrix" GET "/api/projects/risk-matrix/" 0 ""
test_ep "Time Report" GET "/api/projects/time-report/" 0 ""
# --- CRM ---
test_ep "CRM Stats" GET "/api/crm/stats/" 0 ""
test_ep "CRM Tickets" GET "/api/crm/tickets/" 0 ""
test_ep "SLA Policies" GET "/api/crm/sla-policies/" 0 ""
test_ep "Quotations" GET "/api/crm/quotations/" 0 ""
test_ep "Commissions" GET "/api/crm/commissions/" 0 ""
test_ep "Ticket Stats" GET "/api/crm/ticket-stats/" 0 ""
test_ep "Commission Stats" GET "/api/crm/commission-stats/" 0 ""
test_ep "Pipeline Funnel" GET "/api/crm/pipeline/funnel/" 0 ""
test_ep "Sales Forecast" GET "/api/crm/sales-forecast/" 0 ""
# --- POS ---
test_ep "POS Stats" GET "/api/pos/stats/" 0 ""
test_ep "Price Lists" GET "/api/pos/price-lists/" 0 ""
test_ep "Discount Rules" GET "/api/pos/discount-rules/" 0 ""
test_ep "Promo Codes" GET "/api/pos/promo-codes/" 0 ""
test_ep "Loyalty Programs" GET "/api/pos/loyalty-programs/" 0 ""
test_ep "POS Tables" GET "/api/pos/tables/" 0 ""
test_ep "POS Shifts" GET "/api/pos/shifts/" 0 ""
test_ep "Installments" GET "/api/pos/installments/" 0 ""
# --- Accounting ---
test_ep "Acct Accounts" GET "/api/accounting/accounts/" 0 ""
test_ep "Acct Stats" GET "/api/accounting/stats/" 0 ""
test_ep "Acct Entries" GET "/api/accounting/entries/" 0 ""
# --- HR ---
test_ep "HR Employees" GET "/api/hr/employees/" 0 ""
test_ep "HR Departments" GET "/api/hr/departments/" 0 ""
test_ep "HR Stats" GET "/api/hr/stats/" 0 ""
# --- Purchases ---
test_ep "Purchase Orders" GET "/api/purchases/orders/" 0 ""
test_ep "Suppliers" GET "/api/purchases/suppliers/" 0 ""
test_ep "Purchase Stats" GET "/api/purchases/stats/" 0 ""
# --- Invoicing ---
test_ep "Invoices" GET "/api/invoicing/" 0 ""
test_ep "Invoicing Stats" GET "/api/invoicing/stats/" 0 ""
# --- Analytics ---
test_ep "Anomalies" GET "/api/analytics/anomalies/" 0 ""
test_ep "Run Forecast" POST "/api/analytics/run-forecast/" 0 "{}"
# --- Chatbot ---
test_ep "Chatbot Convos" GET "/api/chatbot/conversations/" 0 ""
# --- Notifications ---
test_ep "Notifications" GET "/api/notifications/" 0 ""
# --- Documents ---
test_ep "Documents" GET "/api/documents/" 0 ""
# --- Assets ---
test_ep "Assets" GET "/api/assets/assets/" 0 ""
test_ep "Assets Stats" GET "/api/assets/stats/" 0 ""
# --- Contracts ---
test_ep "Contracts" GET "/api/contracts/" 0 ""
# --- Payments ---
test_ep "Payment Txns" GET "/api/payments/transactions/" 0 ""

echo ""
echo "=== SECTION: WITH AUTH ==="
# --- Auth ---
test_ep "Auth Profile" GET "/api/auth/profile/" 1 ""
test_ep "User List" GET "/api/auth/users/" 1 ""
# --- Sales ---
test_ep "Sales Orders" GET "/api/sales/orders/" 1 ""
test_ep "Sales Customers" GET "/api/sales/customers/" 1 ""
test_ep "Sales Stats" GET "/api/sales/stats/" 1 ""
# --- Projects ---
test_ep "Projects Stats" GET "/api/projects/stats/" 1 ""
test_ep "Projects Phases" GET "/api/projects/phases/" 1 ""
test_ep "Projects Risks" GET "/api/projects/risks/" 1 ""
test_ep "Budget Items" GET "/api/projects/budget-items/" 1 ""
test_ep "Time Entries" GET "/api/projects/time-entries/" 1 ""
test_ep "Proj Contracts" GET "/api/projects/contracts/" 1 ""
test_ep "Proj Documents" GET "/api/projects/documents/" 1 ""
test_ep "Milestones" GET "/api/projects/milestones/" 1 ""
test_ep "Budget Stats" GET "/api/projects/budget-stats/" 1 ""
test_ep "Risk Matrix" GET "/api/projects/risk-matrix/" 1 ""
test_ep "Time Report" GET "/api/projects/time-report/" 1 ""
# --- CRM ---
test_ep "CRM Stats" GET "/api/crm/stats/" 1 ""
test_ep "CRM Tickets" GET "/api/crm/tickets/" 1 ""
test_ep "SLA Policies" GET "/api/crm/sla-policies/" 1 ""
test_ep "Quotations" GET "/api/crm/quotations/" 1 ""
test_ep "Commissions" GET "/api/crm/commissions/" 1 ""
test_ep "Ticket Stats" GET "/api/crm/ticket-stats/" 1 ""
test_ep "Commission Stats" GET "/api/crm/commission-stats/" 1 ""
test_ep "Pipeline Funnel" GET "/api/crm/pipeline/funnel/" 1 ""
test_ep "Sales Forecast" GET "/api/crm/sales-forecast/" 1 ""
# --- POS ---
test_ep "POS Stats" GET "/api/pos/stats/" 1 ""
test_ep "Price Lists" GET "/api/pos/price-lists/" 1 ""
test_ep "Discount Rules" GET "/api/pos/discount-rules/" 1 ""
test_ep "Promo Codes" GET "/api/pos/promo-codes/" 1 ""
test_ep "Loyalty Programs" GET "/api/pos/loyalty-programs/" 1 ""
test_ep "POS Tables" GET "/api/pos/tables/" 1 ""
test_ep "POS Shifts" GET "/api/pos/shifts/" 1 ""
test_ep "Installments" GET "/api/pos/installments/" 1 ""
# --- Accounting ---
test_ep "Acct Accounts" GET "/api/accounting/accounts/" 1 ""
test_ep "Acct Stats" GET "/api/accounting/stats/" 1 ""
test_ep "Acct Entries" GET "/api/accounting/entries/" 1 ""
# --- HR ---
test_ep "HR Employees" GET "/api/hr/employees/" 1 ""
test_ep "HR Departments" GET "/api/hr/departments/" 1 ""
test_ep "HR Stats" GET "/api/hr/stats/" 1 ""
# --- Purchases ---
test_ep "Purchase Orders" GET "/api/purchases/orders/" 1 ""
test_ep "Suppliers" GET "/api/purchases/suppliers/" 1 ""
test_ep "Purchase Stats" GET "/api/purchases/stats/" 1 ""
# --- Invoicing ---
test_ep "Invoices" GET "/api/invoicing/" 1 ""
test_ep "Invoicing Stats" GET "/api/invoicing/stats/" 1 ""
# --- Analytics ---
test_ep "Anomalies" GET "/api/analytics/anomalies/" 1 ""
test_ep "Run Forecast" POST "/api/analytics/run-forecast/" 1 "{}"
# --- Chatbot ---
test_ep "Chatbot Convos" GET "/api/chatbot/conversations/" 1 ""
test_ep "Chatbot Chat" POST "/api/chatbot/chat/" 1 '{"message":"مرحبا"}'
# --- Notifications ---
test_ep "Notifications" GET "/api/notifications/" 1 ""
# --- Documents ---
test_ep "Documents" GET "/api/documents/" 1 ""
# --- Assets ---
test_ep "Assets" GET "/api/assets/assets/" 1 ""
test_ep "Assets Stats" GET "/api/assets/stats/" 1 ""
# --- Contracts ---
test_ep "Contracts" GET "/api/contracts/" 1 ""
# --- Payments ---
test_ep "Payment Txns" GET "/api/payments/transactions/" 1 ""

echo ""
echo "=== SECTION: CRUD ==="
# CRUD tests
test_ep "Phase POST empty" POST "/api/projects/phases/" 1 '{}'
test_ep "Phase POST data" POST "/api/projects/phases/" 1 '{"name":"Test Phase","project":1}'
test_ep "Ticket POST empty" POST "/api/crm/tickets/" 1 '{}'
test_ep "Ticket POST data" POST "/api/crm/tickets/" 1 '{"subject":"Test Ticket","priority":"medium"}'
test_ep "PriceList POST empty" POST "/api/pos/price-lists/" 1 '{}'
test_ep "PriceList POST data" POST "/api/pos/price-lists/" 1 '{"name":"Test Price List"}'
test_ep "SalesOrder POST empty" POST "/api/sales/orders/" 1 '{}'

echo ""
echo "=== SECTION: ERROR HANDLING ==="
# Error handling tests
test_ep "Nonexistent" GET "/api/nonexistent/" 0 ""
test_ep "Invalid method" DELETE "/api/sales/orders/" 0 ""
test_ep "Bad login" POST "/api/auth/login/" 0 '{"username":"bad","password":"bad"}'
test_ep "Invalid proj ID" GET "/api/projects/999999/" 1 ""
test_ep "Invalid user ID" GET "/api/auth/users/999999/" 1 ""
test_ep "Task endpoint /api/auth/me/" GET "/api/auth/me/" 0 ""
test_ep "Task endpoint /api/users/users/" GET "/api/users/users/" 0 ""
test_ep "Task endpoint /api/users/stats/" GET "/api/users/stats/" 0 ""
test_ep "Task endpoint /api/invoicing/invoices/" GET "/api/invoicing/invoices/" 0 ""
test_ep "Task endpoint /api/analytics/forecasting/" GET "/api/analytics/forecasting/" 0 ""
test_ep "Task endpoint /api/documents/documents/" GET "/api/documents/documents/" 0 ""
test_ep "Task endpoint /api/contracts/contracts/" GET "/api/contracts/contracts/" 0 ""
test_ep "Task endpoint /api/payments/payments/" GET "/api/payments/payments/" 0 ""

# Kill server
kill $SERVER_PID 2>/dev/null
echo ""
echo "DONE"
