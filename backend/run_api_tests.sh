#!/bin/bash
# Self-contained API test - starts server, runs tests, kills server
# All in one shell session

cd /home/z/my-project/riadah-erp-v0/backend

# Kill any existing server
pkill -f "manage.py runserver" 2>/dev/null
sleep 1

# Start server in background
python manage.py runserver 0.0.0.0:8000 > /tmp/django_test.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server
sleep 10

# Check if server is up
curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8000/api/auth/login/ > /tmp/server_check.txt 2>/dev/null
if [ "$(cat /tmp/server_check.txt)" = "000" ]; then
    echo "SERVER DID NOT START PROPERLY"
    cat /tmp/django_test.log
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
echo "Server is up"

# Get auth token
TOKEN=$(curl -s --max-time 10 -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access','NO_TOKEN'))" 2>/dev/null)

if [ "$TOKEN" = "NO_TOKEN" ] || [ -z "$TOKEN" ]; then
    echo "TOKEN_FAILED"
    TOKEN=""
fi

echo "Token: ${TOKEN:0:20}..."

# Test function
test_ep() {
    local method="$1" url="$2" token="$3" data="$4" label="$5"
    local start=$(date +%s%N)
    local resp_body=$(mktemp)
    local http_code
    
    if [ -n "$data" ]; then
        http_code=$(curl -s -o "$resp_body" -w "%{http_code}" --max-time 8 \
            -X "$method" -H "Content-Type: application/json" \
            $([ -n "$token" ] && echo "-H 'Authorization: Bearer $token'" || echo "") \
            -d "$data" "http://localhost:8000$url" 2>/dev/null)
    else
        http_code=$(curl -s -o "$resp_body" -w "%{http_code}" --max-time 8 \
            -X "$method" \
            $([ -n "$token" ] && echo "-H 'Authorization: Bearer $token'" || echo "") \
            "http://localhost:8000$url" 2>/dev/null)
    fi
    
    local end=$(date +%s%N)
    local ms=$(( (end - start) / 1000000 ))
    local body=$(head -c 120 "$resp_body" 2>/dev/null)
    rm -f "$resp_body"
    
    echo "${label}|${method}|${url}|${http_code}|${ms}|${body}"
}

echo "NO_AUTH"
# Test without auth
test_ep GET "/api/auth/me/" "" "" "Auth Me"
test_ep GET "/api/users/users/" "" "" "Users List"
test_ep GET "/api/users/stats/" "" "" "Users Stats"
test_ep GET "/api/sales/orders/" "" "" "Sales Orders"
test_ep GET "/api/sales/customers/" "" "" "Sales Customers"
test_ep GET "/api/sales/stats/" "" "" "Sales Stats"
test_ep GET "/api/projects/stats/" "" "" "Projects Stats"
test_ep GET "/api/projects/phases/" "" "" "Project Phases"
test_ep GET "/api/projects/risks/" "" "" "Project Risks"
test_ep GET "/api/projects/budget-items/" "" "" "Budget Items"
test_ep GET "/api/projects/time-entries/" "" "" "Time Entries"
test_ep GET "/api/projects/contracts/" "" "" "Project Contracts"
test_ep GET "/api/projects/documents/" "" "" "Project Documents"
test_ep GET "/api/projects/milestones/" "" "" "Milestones"
test_ep GET "/api/projects/budget-stats/" "" "" "Budget Stats"
test_ep GET "/api/projects/risk-matrix/" "" "" "Risk Matrix"
test_ep GET "/api/projects/time-report/" "" "" "Time Report"
test_ep GET "/api/crm/stats/" "" "" "CRM Stats"
test_ep GET "/api/crm/tickets/" "" "" "CRM Tickets"
test_ep GET "/api/crm/sla-policies/" "" "" "SLA Policies"
test_ep GET "/api/crm/quotations/" "" "" "Quotations"
test_ep GET "/api/crm/commissions/" "" "" "Commissions"
test_ep GET "/api/crm/ticket-stats/" "" "" "Ticket Stats"
test_ep GET "/api/crm/commission-stats/" "" "" "Commission Stats"
test_ep GET "/api/crm/pipeline-funnel/" "" "" "Pipeline Funnel"
test_ep GET "/api/crm/sales-forecast/" "" "" "Sales Forecast"
test_ep GET "/api/pos/stats/" "" "" "POS Stats"
test_ep GET "/api/pos/price-lists/" "" "" "Price Lists"
test_ep GET "/api/pos/discount-rules/" "" "" "Discount Rules"
test_ep GET "/api/pos/promo-codes/" "" "" "Promo Codes"
test_ep GET "/api/pos/loyalty-programs/" "" "" "Loyalty Programs"
test_ep GET "/api/pos/tables/" "" "" "POS Tables"
test_ep GET "/api/pos/shifts/" "" "" "POS Shifts"
test_ep GET "/api/pos/installments/" "" "" "Installments"
test_ep GET "/api/accounting/accounts/" "" "" "Accounting Accounts"
test_ep GET "/api/accounting/stats/" "" "" "Accounting Stats"
test_ep GET "/api/accounting/entries/" "" "" "Accounting Entries"
test_ep GET "/api/hr/employees/" "" "" "HR Employees"
test_ep GET "/api/hr/departments/" "" "" "HR Departments"
test_ep GET "/api/hr/stats/" "" "" "HR Stats"
test_ep GET "/api/purchases/orders/" "" "" "Purchase Orders"
test_ep GET "/api/purchases/suppliers/" "" "" "Suppliers"
test_ep GET "/api/purchases/stats/" "" "" "Purchase Stats"
test_ep GET "/api/invoicing/invoices/" "" "" "Invoices"
test_ep GET "/api/invoicing/stats/" "" "" "Invoicing Stats"
test_ep GET "/api/analytics/forecasting/" "" "" "Analytics Forecasting"
test_ep GET "/api/analytics/anomalies/" "" "" "Analytics Anomalies"
test_ep GET "/api/chatbot/conversations/" "" "" "Chatbot Conversations"
test_ep GET "/api/notifications/" "" "" "Notifications"
test_ep GET "/api/documents/documents/" "" "" "Documents"
test_ep GET "/api/payments/payments/" "" "" "Payments"

echo "WITH_AUTH"
# Test with auth
test_ep GET "/api/auth/me/" "$TOKEN" "" "Auth Me"
test_ep GET "/api/users/users/" "$TOKEN" "" "Users List"
test_ep GET "/api/users/stats/" "$TOKEN" "" "Users Stats"
test_ep GET "/api/sales/orders/" "$TOKEN" "" "Sales Orders"
test_ep GET "/api/sales/customers/" "$TOKEN" "" "Sales Customers"
test_ep GET "/api/sales/stats/" "$TOKEN" "" "Sales Stats"
test_ep GET "/api/projects/stats/" "$TOKEN" "" "Projects Stats"
test_ep GET "/api/projects/phases/" "$TOKEN" "" "Project Phases"
test_ep GET "/api/projects/risks/" "$TOKEN" "" "Project Risks"
test_ep GET "/api/projects/budget-items/" "$TOKEN" "" "Budget Items"
test_ep GET "/api/projects/time-entries/" "$TOKEN" "" "Time Entries"
test_ep GET "/api/projects/contracts/" "$TOKEN" "" "Project Contracts"
test_ep GET "/api/projects/documents/" "$TOKEN" "" "Project Documents"
test_ep GET "/api/projects/milestones/" "$TOKEN" "" "Milestones"
test_ep GET "/api/projects/budget-stats/" "$TOKEN" "" "Budget Stats"
test_ep GET "/api/projects/risk-matrix/" "$TOKEN" "" "Risk Matrix"
test_ep GET "/api/projects/time-report/" "$TOKEN" "" "Time Report"
test_ep GET "/api/crm/stats/" "$TOKEN" "" "CRM Stats"
test_ep GET "/api/crm/tickets/" "$TOKEN" "" "CRM Tickets"
test_ep GET "/api/crm/sla-policies/" "$TOKEN" "" "SLA Policies"
test_ep GET "/api/crm/quotations/" "$TOKEN" "" "Quotations"
test_ep GET "/api/crm/commissions/" "$TOKEN" "" "Commissions"
test_ep GET "/api/crm/ticket-stats/" "$TOKEN" "" "Ticket Stats"
test_ep GET "/api/crm/commission-stats/" "$TOKEN" "" "Commission Stats"
test_ep GET "/api/crm/pipeline-funnel/" "$TOKEN" "" "Pipeline Funnel"
test_ep GET "/api/crm/sales-forecast/" "$TOKEN" "" "Sales Forecast"
test_ep GET "/api/pos/stats/" "$TOKEN" "" "POS Stats"
test_ep GET "/api/pos/price-lists/" "$TOKEN" "" "Price Lists"
test_ep GET "/api/pos/discount-rules/" "$TOKEN" "" "Discount Rules"
test_ep GET "/api/pos/promo-codes/" "$TOKEN" "" "Promo Codes"
test_ep GET "/api/pos/loyalty-programs/" "$TOKEN" "" "Loyalty Programs"
test_ep GET "/api/pos/tables/" "$TOKEN" "" "POS Tables"
test_ep GET "/api/pos/shifts/" "$TOKEN" "" "POS Shifts"
test_ep GET "/api/pos/installments/" "$TOKEN" "" "Installments"
test_ep GET "/api/accounting/accounts/" "$TOKEN" "" "Accounting Accounts"
test_ep GET "/api/accounting/stats/" "$TOKEN" "" "Accounting Stats"
test_ep GET "/api/accounting/entries/" "$TOKEN" "" "Accounting Entries"
test_ep GET "/api/hr/employees/" "$TOKEN" "" "HR Employees"
test_ep GET "/api/hr/departments/" "$TOKEN" "" "HR Departments"
test_ep GET "/api/hr/stats/" "$TOKEN" "" "HR Stats"
test_ep GET "/api/purchases/orders/" "$TOKEN" "" "Purchase Orders"
test_ep GET "/api/purchases/suppliers/" "$TOKEN" "" "Suppliers"
test_ep GET "/api/purchases/stats/" "$TOKEN" "" "Purchase Stats"
test_ep GET "/api/invoicing/invoices/" "$TOKEN" "" "Invoices"
test_ep GET "/api/invoicing/stats/" "$TOKEN" "" "Invoicing Stats"
test_ep GET "/api/analytics/forecasting/" "$TOKEN" "" "Analytics Forecasting"
test_ep GET "/api/analytics/anomalies/" "$TOKEN" "" "Analytics Anomalies"
test_ep GET "/api/chatbot/conversations/" "$TOKEN" "" "Chatbot Conversations"
test_ep GET "/api/notifications/" "$TOKEN" "" "Notifications"
test_ep GET "/api/documents/documents/" "$TOKEN" "" "Documents"
test_ep GET "/api/payments/payments/" "$TOKEN" "" "Payments"

echo "CRUD"
# CRUD tests
test_ep POST "/api/chatbot/chat/" "$TOKEN" '{"message":"مرحبا"}' "Chatbot POST"
test_ep POST "/api/projects/phases/" "$TOKEN" '{}' "Phase POST empty"
test_ep POST "/api/projects/phases/" "$TOKEN" '{"name":"Test Phase","project":1}' "Phase POST with data"
test_ep POST "/api/crm/tickets/" "$TOKEN" '{}' "Ticket POST empty"
test_ep POST "/api/crm/tickets/" "$TOKEN" '{"subject":"Test Ticket","priority":"medium"}' "Ticket POST with data"
test_ep POST "/api/pos/price-lists/" "$TOKEN" '{}' "PriceList POST empty"
test_ep POST "/api/pos/price-lists/" "$TOKEN" '{"name":"Test Price List"}' "PriceList POST with data"
test_ep POST "/api/sales/orders/" "$TOKEN" '{}' "SalesOrder POST empty"

echo "ERRORS"
# Error handling
test_ep GET "/api/nonexistent/" "" "" "Nonexistent endpoint"
test_ep DELETE "/api/sales/orders/" "" "" "Invalid method DELETE"
test_ep POST "/api/auth/login/" "" '{"username":"bad","password":"bad"}' "Login bad creds"
test_ep GET "/api/projects/999999/" "$TOKEN" "" "Invalid project ID"
test_ep GET "/api/users/999999/" "$TOKEN" "" "Invalid user ID"

# Kill server
kill $SERVER_PID 2>/dev/null
echo "DONE"
