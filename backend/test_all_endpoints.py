#!/usr/bin/env python3
"""
Comprehensive API endpoint test script for RIADAH ERP v0
Tests chatbot, analytics, CRM, and dashboard endpoints.
"""
import subprocess
import time
import json
import sys
import os
import signal

BASE_URL = "http://localhost:8000"

def get_token():
    """Get JWT token for admin user."""
    import urllib.request
    data = json.dumps({"username": "admin", "password": "Admin@123"}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login/",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("access", "")
    except Exception as e:
        return ""

def api_call(method, path, token=None, data=None):
    """Make an API call and return (status_code, response_dict_or_error)."""
    import urllib.request
    import urllib.error
    
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode()
            try:
                return resp.status, json.loads(content)
            except json.JSONDecodeError:
                return resp.status, {"raw": content[:500]}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
            return e.code, json.loads(body)
        except:
            return e.code, {"error": body[:500]}
    except Exception as e:
        return 0, {"error": str(e)}

def test_endpoint(method, path, token=None, data=None, label=""):
    """Test a single endpoint and print results."""
    if label:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"  {method} {path}")
        print(f"{'='*60}")
    
    status, response = api_call(method, path, token, data)
    print(f"  HTTP Status: {status}")
    
    # Print response structure
    if isinstance(response, dict):
        keys = list(response.keys())
        print(f"  Response Keys: {keys}")
        # Print truncated response
        resp_str = json.dumps(response, ensure_ascii=False, indent=2)
        if len(resp_str) > 600:
            resp_str = resp_str[:600] + "\n  ... (truncated)"
        print(f"  Response:\n{resp_str}")
    else:
        print(f"  Response: {str(response)[:500]}")
    
    return status, response

def main():
    os.chdir("/home/z/my-project/riadah-erp-v0/backend")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    
    # Get token
    print("Obtaining JWT token...")
    token = get_token()
    if not token:
        print("FATAL: Could not obtain JWT token!")
        sys.exit(1)
    print(f"Token obtained: {token[:30]}...")
    
    results = {}
    
    # =============================================
    # CHATBOT ENDPOINTS
    # =============================================
    print("\n" + "#"*60)
    print("#  CHATBOT ENDPOINTS")
    print("#"*60)
    
    s, r = test_endpoint("POST", "/api/chatbot/chat/", token, 
                          {"message": "مرحباً"}, 
                          "1. Chatbot - Greeting")
    results["chatbot_chat_greeting"] = {"status": s, "response": r}
    
    s, r = test_endpoint("POST", "/api/chatbot/chat/", token,
                          {"message": "كم المبيعات اليوم"},
                          "2. Chatbot - Sales query (today)")
    results["chatbot_chat_sales_today"] = {"status": s, "response": r}
    
    s, r = test_endpoint("POST", "/api/chatbot/chat/", token,
                          {"message": "كم عدد الموظفين"},
                          "3. Chatbot - HR query")
    results["chatbot_chat_hr"] = {"status": s, "response": r}
    
    s, r = test_endpoint("POST", "/api/chatbot/chat/", token,
                          {"message": "كم الأرباح"},
                          "4. Chatbot - Financial query")
    results["chatbot_chat_financial"] = {"status": s, "response": r}
    
    s, r = test_endpoint("POST", "/api/chatbot/chat/", token,
                          {"message": "ما هو النظام"},
                          "5. Chatbot - General question")
    results["chatbot_chat_general"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/chatbot/conversations/", token,
                          label="6. Chatbot - List conversations")
    results["chatbot_conversations_list"] = {"status": s, "response": r}
    
    s, r = test_endpoint("POST", "/api/chatbot/conversations/", token,
                          {"title": "محادثة اختبار"},
                          "7. Chatbot - Create conversation")
    results["chatbot_conversations_create"] = {"status": s, "response": r}
    
    # Get conversation_id from creation response
    conv_id = r.get("id") if isinstance(r, dict) else None
    if conv_id:
        s, r = test_endpoint("GET", f"/api/chatbot/conversations/{conv_id}/", token,
                              label=f"8. Chatbot - Conversation detail ({conv_id})")
        results["chatbot_conversation_detail"] = {"status": s, "response": r}
    else:
        print("\n  [SKIP] No conversation_id available for detail test")
        results["chatbot_conversation_detail"] = {"status": "SKIPPED", "response": None}
    
    # Test history endpoint (same as detail)
    if conv_id:
        s, r = test_endpoint("GET", f"/api/chatbot/conversations/{conv_id}/", token,
                              label=f"9. Chatbot - History ({conv_id})")
        results["chatbot_history"] = {"status": s, "response": r}
    
    # =============================================
    # SMART ANALYTICS ENDPOINTS
    # =============================================
    print("\n" + "#"*60)
    print("#  SMART ANALYTICS ENDPOINTS")
    print("#"*60)
    
    s, r = test_endpoint("GET", "/api/analytics/forecasting/sales/", token,
                          label="10. Sales Forecasting")
    results["analytics_sales_forecast"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/analytics/forecasting/cashflow/", token,
                          label="11. Cashflow Forecasting")
    results["analytics_cashflow_forecast"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/analytics/anomaly/sales/", token,
                          label="12. Sales Anomaly Detection")
    results["analytics_sales_anomaly"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/analytics/anomaly/expenses/", token,
                          label="13. Expense Anomaly Detection")
    results["analytics_expense_anomaly"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/analytics/segmentation/customers/", token,
                          label="14. Customer Segmentation")
    results["analytics_customer_segmentation"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/analytics/segmentation/suppliers/", token,
                          label="15. Supplier Evaluation")
    results["analytics_supplier_evaluation"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/analytics/classification/invoice-risk/", token,
                          label="16. Invoice Risk Classification")
    results["analytics_invoice_risk"] = {"status": s, "response": r}
    
    # =============================================
    # CRM ANALYTICS ENDPOINTS
    # =============================================
    print("\n" + "#"*60)
    print("#  CRM ANALYTICS ENDPOINTS")
    print("#"*60)
    
    s, r = test_endpoint("GET", "/api/crm/stats/", token,
                          label="17. CRM Stats")
    results["crm_stats"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/crm/top-reps/", token,
                          label="18. CRM Top Reps")
    results["crm_top_reps"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/crm/lead-sources/", token,
                          label="19. CRM Lead Sources")
    results["crm_lead_sources"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/crm/sales-stage-analytics/", token,
                          label="20. CRM Sales Stage Analytics")
    results["crm_sales_stage"] = {"status": s, "response": r}
    
    # =============================================
    # DASHBOARD ANALYTICS ENDPOINTS
    # =============================================
    print("\n" + "#"*60)
    print("#  DASHBOARD ANALYTICS ENDPOINTS")
    print("#"*60)
    
    s, r = test_endpoint("GET", "/api/dashboard/live-stats/", token,
                          label="21. Dashboard Live Stats")
    results["dashboard_live_stats"] = {"status": s, "response": r}
    
    s, r = test_endpoint("GET", "/api/core/sales-analytics/", token,
                          label="22. Core Sales Analytics")
    results["core_sales_analytics"] = {"status": s, "response": r}
    
    # =============================================
    # SUMMARY
    # =============================================
    print("\n" + "#"*60)
    print("#  SUMMARY")
    print("#"*60)
    
    status_counts = {}
    for name, info in results.items():
        st = info["status"]
        status_counts[st] = status_counts.get(st, 0) + 1
    
    for st, count in sorted(status_counts.items()):
        print(f"  HTTP {st}: {count} endpoints")
    
    print(f"\n  Total endpoints tested: {len(results)}")
    
    # Save results
    with open("/tmp/api_test_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print("\n  Full results saved to /tmp/api_test_results.json")

if __name__ == "__main__":
    main()
