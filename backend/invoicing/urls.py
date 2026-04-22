from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.InvoiceStatsView.as_view(), name='invoice-stats'),
    path('', views.InvoiceListView.as_view(), name='invoices'),
    path('create/', views.InvoiceCreateView.as_view(), name='invoice-create'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('<int:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice-update'),
    path('<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice-delete'),
    path('<int:pk>/restore/', views.InvoiceRestoreView.as_view(), name='invoice-restore'),
    path('<int:pk>/change-status/', views.InvoiceChangeStatusView.as_view(), name='invoice-change-status'),
    path('<int:pk>/send/', views.InvoiceSendView.as_view(), name='invoice-send'),
    path('<int:pk>/duplicate/', views.InvoiceDuplicateView.as_view(), name='invoice-duplicate'),
    path('<int:pk>/payments/', views.PaymentListView.as_view(), name='invoice-payments'),
    path('<int:pk>/payments/create/', views.PaymentCreateView.as_view(), name='payment-create'),
    path('payments/<int:payment_pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<int:payment_pk>/update/', views.PaymentUpdateView.as_view(), name='payment-update'),
    path('payments/<int:payment_pk>/delete/', views.PaymentDeleteView.as_view(), name='payment-delete'),
    path('<int:pk>/reminders/', views.ReminderListView.as_view(), name='invoice-reminders'),
    path('<int:pk>/reminders/create/', views.ReminderCreateView.as_view(), name='reminder-create'),
    path('reminders/<int:reminder_pk>/', views.ReminderDetailView.as_view(), name='reminder-detail'),
    path('reminders/<int:reminder_pk>/update/', views.ReminderUpdateView.as_view(), name='reminder-update'),
    path('reminders/<int:reminder_pk>/delete/', views.ReminderDeleteView.as_view(), name='reminder-delete'),
    path('export/', views.InvoiceExportView.as_view(), name='invoice-export'),
]
