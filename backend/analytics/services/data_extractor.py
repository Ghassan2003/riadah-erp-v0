"""Data extraction utilities - converts Django ORM queries to pandas DataFrames.
Uses DB-level aggregation (TruncMonth, TruncDate, annotate) for performance.
Updated to support all 23 current ERP modules (post-cleanup)."""

import pandas as pd
import logging
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Max, Min, Q, F, Case, When, Value, DecimalField
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, Coalesce

logger = logging.getLogger(__name__)


def decimal_to_float(val):
    """Convert Decimal to float for pandas compatibility."""
    if val is None:
        return 0.0
    return float(val)


def get_daily_sales(start_date=None, end_date=None):
    """Get daily sales totals using DB-level aggregation.
    Returns DataFrame with columns: date, total_amount, order_count
    """
    from sales.models import SalesOrder

    qs = SalesOrder.objects.filter(
        status__in=['confirmed', 'delivered']
    )
    if start_date:
        qs = qs.filter(order_date__gte=start_date)
    if end_date:
        qs = qs.filter(order_date__lte=end_date)

    # Fetch raw values and group in pandas (avoids SQLite TruncDate issues)
    rows = qs.values_list('order_date', 'total_amount', 'id')

    if not rows:
        return pd.DataFrame(columns=['date', 'total_amount', 'order_count'])

    df = pd.DataFrame(rows, columns=['date', 'total_amount', 'order_id'])
    df['date'] = pd.to_datetime(df['date'])
    df['total_amount'] = df['total_amount'].apply(decimal_to_float)

    daily = df.groupby('date').agg(
        total_amount=('total_amount', 'sum'),
        order_count=('order_id', 'count')
    ).reset_index()

    return daily


def get_monthly_sales(years=None):
    """Get monthly sales totals.
    Returns DataFrame with columns: month, total_amount, order_count
    """
    from sales.models import SalesOrder

    qs = SalesOrder.objects.filter(status__in=['confirmed', 'delivered'])
    if years:
        qs = qs.filter(order_date__year__in=years)

    data = qs.annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        total_amount=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
        order_count=Count('id')
    ).order_by('month')

    if not data:
        return pd.DataFrame(columns=['month', 'total_amount', 'order_count'])

    df = pd.DataFrame(list(data))
    df['month'] = pd.to_datetime(df['month'])
    df['total_amount'] = df['total_amount'].apply(decimal_to_float)
    return df


def get_product_demand(top_n=20):
    """Get weekly demand per product.
    Returns DataFrame with columns: week, product_name, product_id, quantity
    """
    from sales.models import SalesOrderItem

    qs = SalesOrderItem.objects.filter(
        order__status__in=['confirmed', 'delivered']
    ).annotate(
        week=TruncWeek('order__order_date')
    ).values('week', 'product_name', 'product_id').annotate(
        quantity=Coalesce(Sum('quantity'), 0)
    ).order_by('product_name', 'week')

    if not qs.exists():
        return pd.DataFrame(columns=['week', 'product_name', 'product_id', 'quantity'])

    df = pd.DataFrame(list(qs))
    df['week'] = pd.to_datetime(df['week'])

    # Get top N products by total demand
    top_products = df.groupby('product_name')['quantity'].sum().nlargest(top_n).index
    df = df[df['product_name'].isin(top_products)]

    return df


def get_cashflow_data(start_date=None):
    """Get monthly cash flow (inflows - outflows).
    Returns DataFrame with columns: month, inflow, outflow, net
    """
    from invoicing.models import Payment, Invoice

    qs = Payment.objects.all()
    if start_date:
        qs = qs.filter(payment_date__gte=start_date)

    data = qs.annotate(
        month=TruncMonth('payment_date')
    ).values('month', 'invoice__invoice_type').annotate(
        total=Coalesce(Sum('amount'), Value(0, output_field=DecimalField()))
    ).order_by('month')

    if not data:
        return pd.DataFrame(columns=['month', 'inflow', 'outflow', 'net'])

    df = pd.DataFrame(list(data))
    df['month'] = pd.to_datetime(df['month'])
    df['total'] = df['total'].apply(decimal_to_float)

    # Pivot: sales invoices = inflow, purchase invoices = outflow
    pivot = df.pivot_table(index='month', columns='invoice__invoice_type', values='total', fill_value=0)
    pivot = pivot.reset_index()

    result = pd.DataFrame({'month': pivot['month']})
    result['inflow'] = pivot.get('sales', 0) + pivot.get('credit_note', 0)
    result['outflow'] = pivot.get('purchase', 0) + pivot.get('debit_note', 0)
    result['net'] = result['inflow'] - result['outflow']
    return result


def get_expense_transactions(start_date=None):
    """Get daily expense totals from accounting transactions.
    Returns DataFrame with columns: date, amount, account_code, account_name
    """
    from accounting.models import Transaction

    qs = Transaction.objects.filter(
        journal_entry__is_posted=True,
        account__account_type='expense'
    ).select_related('account', 'journal_entry')
    if start_date:
        qs = qs.filter(journal_entry__entry_date__gte=start_date)

    # Fetch flat values and group in pandas (avoids SQLite TruncDate issues)
    rows = qs.values_list(
        'journal_entry__entry_date', 'amount',
        'account__code', 'account__name', 'journal_entry__description'
    )

    if not rows:
        return pd.DataFrame(columns=['date', 'amount', 'account_code', 'account_name', 'description'])

    df = pd.DataFrame(rows, columns=['date', 'amount', 'account_code', 'account_name', 'description'])
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = df['amount'].apply(decimal_to_float)

    # Group by date and account
    grouped = df.groupby(['date', 'account_code', 'account_name']).agg(
        amount=('amount', 'sum'),
        description=('description', 'first')
    ).reset_index()

    return grouped


def get_customer_rfm_data():
    """Get RFM (Recency, Frequency, Monetary) data for all customers.
    Returns DataFrame with columns: customer_id, customer_name, recency_days, frequency, monetary
    """
    from sales.models import Customer, SalesOrder
    from django.utils import timezone

    data = Customer.objects.annotate(
        frequency=Count('orders', filter=Q(orders__status__in=['confirmed', 'delivered'])),
        monetary=Coalesce(Sum('orders__total_amount', filter=Q(orders__status__in=['confirmed', 'delivered'])), Value(0, output_field=DecimalField())),
        last_order=Max('orders__order_date', filter=Q(orders__status__in=['confirmed', 'delivered'])),
        first_order=Min('orders__order_date', filter=Q(orders__status__in=['confirmed', 'delivered'])),
    ).filter(
        frequency__gt=0
    ).values('id', 'name', 'email', 'frequency', 'monetary', 'last_order', 'first_order')

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(list(data))
    df['last_order'] = pd.to_datetime(df['last_order'])
    df['first_order'] = pd.to_datetime(df['first_order'])
    now_naive = pd.Timestamp.now(tz='UTC').tz_localize(None)
    df['recency_days'] = (now_naive - df['last_order']).dt.days.fillna(9999).astype(int)
    df['monetary'] = df['monetary'].apply(decimal_to_float)
    df = df.rename(columns={'id': 'customer_id', 'name': 'customer_name'})
    return df


def get_supplier_evaluation_data():
    """Get supplier performance data.
    Returns DataFrame with columns: supplier_id, supplier_name, total_orders, total_amount,
    avg_delivery_days, fill_rate
    """
    from purchases.models import Supplier, PurchaseOrder, PurchaseOrderItem

    # Order metrics
    order_data = PurchaseOrder.objects.filter(
        status__in=['confirmed', 'received', 'partial']
    ).values('supplier__id', 'supplier__name').annotate(
        total_orders=Count('id'),
        total_amount=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
    )

    # Fill rate - use raw values_list to avoid mixed type issues
    fill_rows = PurchaseOrderItem.objects.values_list(
        'order__supplier__id', 'quantity', 'received_quantity'
    )
    # Aggregate in Python
    from collections import defaultdict
    fill_data = defaultdict(lambda: {'ordered_qty': 0, 'received_qty': 0})
    for sid, qty, recv in fill_rows:
        fill_data[sid]['ordered_qty'] += float(qty)
        fill_data[sid]['received_qty'] += float(recv)

    if not order_data:
        return pd.DataFrame()

    rows = []
    for item in order_data:
        sid = item['supplier__id']
        fill = fill_data.get(sid, {'ordered_qty': 0, 'received_qty': 0})
        ordered = fill['ordered_qty']
        received = fill['received_qty']
        rows.append({
            'supplier_id': sid,
            'supplier_name': item['supplier__name'],
            'total_orders': item['total_orders'],
            'total_amount': decimal_to_float(item['total_amount']),
            'fill_rate': (received / ordered * 100) if ordered > 0 else 0,
        })

    return pd.DataFrame(rows)


# ── CRM Analytics Data ────────────────────────────────────────────────


def get_crm_pipeline_data():
    """Get CRM sales pipeline data.
    Returns DataFrame with columns: stage, count, total_value
    """
    try:
        from crm.models import Lead
    except ImportError:
        return pd.DataFrame(columns=['stage', 'count', 'total_value'])

    data = Lead.objects.filter(
        is_active=True
    ).values('stage').annotate(
        count=Count('id'),
        total_value=Coalesce(Sum('estimated_value'), Value(0, output_field=DecimalField()))
    ).order_by('stage')

    if not data:
        return pd.DataFrame(columns=['stage', 'count', 'total_value'])

    df = pd.DataFrame(list(data))
    df['total_value'] = df['total_value'].apply(decimal_to_float)
    return df


def get_crm_tickets_data(start_date=None):
    """Get CRM support tickets data.
    Returns DataFrame with columns: status, count, avg_resolution_hours
    """
    try:
        from crm.models import Ticket
    except ImportError:
        return pd.DataFrame(columns=['status', 'count', 'avg_resolution_hours'])

    qs = Ticket.objects.all()
    if start_date:
        qs = qs.filter(created_at__gte=start_date)

    data = qs.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    if not data:
        return pd.DataFrame(columns=['status', 'count'])

    df = pd.DataFrame(list(data))
    return df


# ── POS Analytics Data ────────────────────────────────────────────────


def get_pos_daily_sales(start_date=None):
    """Get daily POS sales totals.
    Returns DataFrame with columns: date, total_amount, transaction_count
    """
    try:
        from pos.models import Sale
    except ImportError:
        return pd.DataFrame(columns=['date', 'total_amount', 'transaction_count'])

    qs = Sale.objects.all()
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)

    rows = qs.values_list('created_at__date', 'total_amount', 'id')
    if not rows:
        return pd.DataFrame(columns=['date', 'total_amount', 'transaction_count'])

    df = pd.DataFrame(rows, columns=['date', 'total_amount', 'sale_id'])
    df['date'] = pd.to_datetime(df['date'])
    df['total_amount'] = df['total_amount'].apply(decimal_to_float)

    daily = df.groupby('date').agg(
        total_amount=('total_amount', 'sum'),
        transaction_count=('sale_id', 'count')
    ).reset_index()

    return daily


def get_pos_top_products(top_n=10):
    """Get top selling products from POS.
    Returns DataFrame with columns: product_name, quantity, revenue
    """
    try:
        from pos.models import SaleItem
    except ImportError:
        return pd.DataFrame(columns=['product_name', 'quantity', 'revenue'])

    data = SaleItem.objects.values('product_name').annotate(
        quantity=Coalesce(Sum('quantity'), 0),
        revenue=Coalesce(Sum('total'), Value(0, output_field=DecimalField()))
    ).order_by('-quantity')[:top_n]

    if not data:
        return pd.DataFrame(columns=['product_name', 'quantity', 'revenue'])

    df = pd.DataFrame(list(data))
    df['revenue'] = df['revenue'].apply(decimal_to_float)
    return df


# ── Projects Analytics Data ──────────────────────────────────────────


def get_projects_status_data():
    """Get projects status distribution.
    Returns DataFrame with columns: status, count, total_budget, total_spent
    """
    try:
        from projects.models import Project
    except ImportError:
        return pd.DataFrame(columns=['status', 'count', 'total_budget', 'total_spent'])

    data = Project.objects.values('status').annotate(
        count=Count('id'),
        total_budget=Coalesce(Sum('budget'), Value(0, output_field=DecimalField())),
        total_spent=Coalesce(Sum('spent'), Value(0, output_field=DecimalField()))
    ).order_by('status')

    if not data:
        return pd.DataFrame(columns=['status', 'count', 'total_budget', 'total_spent'])

    df = pd.DataFrame(list(data))
    df['total_budget'] = df['total_budget'].apply(decimal_to_float)
    df['total_spent'] = df['total_spent'].apply(decimal_to_float)
    return df


def get_projects_risk_data():
    """Get project risks summary.
    Returns DataFrame with columns: severity, count
    """
    try:
        from projects.models import Risk
    except ImportError:
        return pd.DataFrame(columns=['severity', 'count'])

    data = Risk.objects.values('severity').annotate(
        count=Count('id')
    ).order_by('-count')

    if not data:
        return pd.DataFrame(columns=['severity', 'count'])

    return pd.DataFrame(list(data))


# ── Payroll Analytics Data ────────────────────────────────────────────


def get_payroll_summary_data():
    """Get payroll summary data.
    Returns DataFrame with columns: month, total_gross, total_deductions, total_net, employee_count
    """
    try:
        from payroll.models import Payslip
    except ImportError:
        return pd.DataFrame(columns=['month', 'total_gross', 'total_deductions', 'total_net', 'employee_count'])

    data = Payslip.objects.annotate(
        month=TruncMonth('pay_period_start')
    ).values('month').annotate(
        total_gross=Coalesce(Sum('gross_pay'), Value(0, output_field=DecimalField())),
        total_deductions=Coalesce(Sum('total_deductions'), Value(0, output_field=DecimalField())),
        total_net=Coalesce(Sum('net_pay'), Value(0, output_field=DecimalField())),
        employee_count=Count('id')
    ).order_by('month')

    if not data:
        return pd.DataFrame(columns=['month', 'total_gross', 'total_deductions', 'total_net', 'employee_count'])

    df = pd.DataFrame(list(data))
    df['month'] = pd.to_datetime(df['month'])
    df['total_gross'] = df['total_gross'].apply(decimal_to_float)
    df['total_deductions'] = df['total_deductions'].apply(decimal_to_float)
    df['total_net'] = df['total_net'].apply(decimal_to_float)
    return df
