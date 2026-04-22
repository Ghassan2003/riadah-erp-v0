"""
Audit Log Middleware - Automatically logs all API operations.
Tracks create, update, delete, status changes, and login/logout.
For update operations (PUT/PATCH), captures old and new values to show
exactly what changed.
"""

import json
import logging
from decimal import Decimal

from django.apps import apps
from django.db import models as django_models
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

# Methods that should be logged
LOGGED_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

# Paths to skip (auth endpoints handled separately)
SKIP_PATHS = {
    '/api/auth/login/',
    '/api/auth/refresh/',
    '/api/auth/change-password/',
    '/api/auth/profile/',
    '/api/notifications/',
}

# URL path to model name mapping (used for display in audit log)
PATH_MODEL_MAP = {
    '/api/inventory/products/': 'Product',
    '/api/sales/customers/': 'Customer',
    '/api/sales/orders/': 'SalesOrder',
    '/api/purchases/suppliers/': 'Supplier',
    '/api/purchases/orders/': 'PurchaseOrder',
    '/api/accounting/accounts/': 'Account',
    '/api/accounting/entries/': 'JournalEntry',
    '/api/hr/departments/': 'Department',
    '/api/hr/employees/': 'Employee',
    '/api/hr/attendance/': 'Attendance',
    '/api/hr/leaves/': 'LeaveRequest',
    '/api/documents/': 'Document',
    '/api/projects/': 'Project',
    '/api/projects/tasks/': 'ProjectTask',
    '/api/projects/expenses/': 'ProjectExpense',
    '/api/auth/users/': 'User',
    '/api/audit-log/': 'AuditLog',
}

# URL path to (app_label, model_name) mapping for dynamic model loading.
# Used by the middleware to fetch existing objects for old/new value comparison.
MODEL_MAP = {
    '/api/inventory/products/': ('inventory', 'Product'),
    '/api/sales/customers/': ('sales', 'Customer'),
    '/api/sales/orders/': ('sales', 'SalesOrder'),
    '/api/purchases/suppliers/': ('purchases', 'Supplier'),
    '/api/purchases/orders/': ('purchases', 'PurchaseOrder'),
    '/api/accounting/accounts/': ('accounting', 'Account'),
    '/api/accounting/entries/': ('accounting', 'JournalEntry'),
    '/api/hr/employees/': ('hr', 'Employee'),
    '/api/hr/departments/': ('hr', 'Department'),
    '/api/projects/': ('projects', 'Project'),
    '/api/auth/users/': ('users', 'User'),
}

# Fields to skip when serializing model instances (sensitive data)
SENSITIVE_FIELD_NAMES = {'password', 'token', 'secret', 'ssn', 'credit_card'}

# Fields that are auto-managed and not meaningful to track in change diffs
AUTO_FIELDS = {'id', 'created_at', 'updated_at'}


def get_model_name(path):
    """Determine model name from URL path."""
    for url_path, model_name in PATH_MODEL_MAP.items():
        if path.startswith(url_path):
            return model_name
    return 'Unknown'


def get_action_from_method_and_path(method, path):
    """Determine action type from HTTP method and URL path."""
    if 'soft-delete' in path or 'toggle-active' in path:
        return 'soft_delete'
    if 'restore' in path:
        return 'restore'
    if 'change-status' in path or 'approve' in path or 'post' in path or 'reverse' in path:
        return 'status_change'

    action_map = {
        'POST': 'create',
        'PUT': 'update',
        'PATCH': 'update',
        'DELETE': 'delete',
    }
    return action_map.get(method, 'other')


def extract_object_id(path, base_url):
    """
    Extract the object ID from a URL path given its base URL prefix.

    Examples:
        extract_object_id('/api/inventory/products/42/', '/api/inventory/products/') -> 42
        extract_object_id('/api/sales/orders/5/change-status/', '/api/sales/orders/') -> 5
        extract_object_id('/api/sales/orders/', '/api/sales/orders/') -> None
    """
    remainder = path[len(base_url):]
    parts = remainder.strip('/').split('/')
    if parts and parts[0].isdigit():
        return int(parts[0])
    return None


def resolve_model_for_path(path):
    """
    Given a URL path, return the Django model class and the matched base URL.

    Returns (model_class, base_url) or (None, None) if no match.
    """
    # Sort by longest prefix first to match the most specific path
    sorted_paths = sorted(MODEL_MAP.keys(), key=len, reverse=True)
    for base_url in sorted_paths:
        if path.startswith(base_url):
            app_label, model_name = MODEL_MAP[base_url]
            try:
                model_class = apps.get_model(app_label, model_name)
                return model_class, base_url
            except LookupError:
                logger.debug(
                    f'AuditLog: model {app_label}.{model_name} not found '
                    f'(path={path})'
                )
                return None, base_url
    return None, None


def _serialize_field_value(value, field):
    """
    Convert a single model field value to a JSON-serializable Python type.
    """
    if value is None:
        return None

    # ForeignKey, OneToOne -> store the related object's pk
    if isinstance(field, (django_models.ForeignKey, django_models.OneToOneField)):
        if hasattr(value, 'pk'):
            return value.pk
        return value

    # ManyToMany -> store list of pks
    if isinstance(field, django_models.ManyToManyField):
        if hasattr(value, 'all'):
            return list(value.values_list('pk', flat=True))
        return list(value) if value else []

    # DateTime / Date / Time -> ISO string
    if isinstance(field, django_models.DateTimeField):
        return value.isoformat() if hasattr(value, 'isoformat') else str(value)

    if isinstance(field, django_models.DateField):
        return value.isoformat() if hasattr(value, 'isoformat') else str(value)

    if isinstance(field, django_models.TimeField):
        return value.isoformat() if hasattr(value, 'isoformat') else str(value)

    # Decimal -> string to preserve precision
    if isinstance(field, django_models.DecimalField):
        return str(value)

    # UUID -> string
    if isinstance(field, django_models.UUIDField):
        return str(value)

    # Duration -> total seconds as string
    if isinstance(field, django_models.DurationField):
        return str(value)

    # JSONField -> already serializable
    if isinstance(field, django_models.JSONField):
        return value

    # Binary fields -> skip (not human-readable)
    if isinstance(field, django_models.BinaryField):
        return '<binary data>'

    # File fields -> filename string
    if isinstance(field, django_models.FileField):
        return str(value)

    # Fallback: try JSON serialization, fall back to str()
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError, OverflowError):
        return str(value)


def serialize_instance(instance):
    """
    Convert a Django model instance to a JSON-serializable dict of its
    concrete field values.  Sensitive fields (password, token, …) are
    omitted.
    """
    data = {}
    for field in instance._meta.get_fields():
        # Only consider concrete, non-auto fields
        if field.auto_created or not field.concrete:
            continue

        field_name = field.name

        # Skip sensitive fields
        if any(sensitive in field_name.lower() for sensitive in SENSITIVE_FIELD_NAMES):
            continue

        try:
            value = getattr(instance, field_name)
            data[field_name] = _serialize_field_value(value, field)
        except Exception:
            # If a single field fails, skip it rather than breaking the whole thing
            data[field_name] = '<error reading field>'

    return data


def fetch_instance(model_class, object_id):
    """
    Fetch a model instance by pk, trying multiple manager strategies to
    handle soft-delete and custom managers gracefully.

    Returns the instance or None.
    """
    if model_class is None or object_id is None:
        return None

    # Strategy 1: use _base_manager (usually the unfiltered manager)
    try:
        return model_class._base_manager.get(pk=object_id)
    except ObjectDoesNotExist:
        pass
    except Exception:
        pass

    # Strategy 2: some apps expose an all_objects manager (e.g. Product)
    if hasattr(model_class, 'all_objects'):
        try:
            return model_class.all_objects.get(pk=object_id)
        except ObjectDoesNotExist:
            pass
        except Exception:
            pass

    # Strategy 3: fall back to _default_manager
    try:
        return model_class._default_manager.get(pk=object_id)
    except ObjectDoesNotExist:
        pass
    except Exception:
        pass

    return None


def compute_changes(old_values, new_values):
    """
    Compare old and new value dicts and return a summary of changed fields.

    Returns a dict: {field_name: {'old': <old_value>, 'new': <new_value>}}
    Only fields whose values actually differ are included.  Auto-managed
    fields (id, created_at, updated_at) are excluded from the diff.
    """
    if not old_values or not new_values:
        return {}

    changes = {}
    # Iterate over the union of keys so we capture fields added or removed
    all_keys = set(old_values.keys()) | set(new_values.keys())

    for key in all_keys:
        # Skip auto-managed fields in the diff
        if key in AUTO_FIELDS:
            continue

        old_val = old_values.get(key)
        new_val = new_values.get(key)

        # Normalize for comparison — handle Decimal vs string mismatch
        old_cmp = _normalize_for_compare(old_val)
        new_cmp = _normalize_for_compare(new_val)

        if old_cmp != new_cmp:
            changes[key] = {'old': old_val, 'new': new_val}

    return changes


def _normalize_for_compare(value):
    """
    Normalize a value for equality comparison.
    Handles cases like Decimal vs string (e.g. "10.00" vs "10").
    """
    if value is None:
        return None

    # If the value is a string that looks like a number, compare as float
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    # Decimal -> float for comparison
    if isinstance(value, Decimal):
        return float(value)

    return value


class AuditLogMiddleware:
    """
    Middleware that runs BEFORE the view is called.
    For PUT/PATCH requests, it fetches the existing object and stores its
    field values on the request so the response middleware can compare
    old vs new.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only pre-fetch for update operations
        if request.method in ('PUT', 'PATCH'):
            self._capture_old_values(request)

        response = self.get_response(request)
        return response

    def _capture_old_values(self, request):
        """
        For PUT/PATCH requests, determine the target model and object,
        then serialize its current state and attach it to the request.
        """
        path = request.path
        if not path.startswith('/api/'):
            return

        # Skip auth endpoints
        for skip_path in SKIP_PATHS:
            if path.startswith(skip_path) or path == skip_path:
                return

        model_class, base_url = resolve_model_for_path(path)
        if model_class is None or base_url is None:
            return

        object_id = extract_object_id(path, base_url)
        if object_id is None:
            return

        try:
            instance = fetch_instance(model_class, object_id)
            if instance is not None:
                request._audit_old_values = serialize_instance(instance)
                request._audit_instance = instance
            else:
                request._audit_old_values = None
                request._audit_instance = None
        except Exception as exc:
            logger.debug(
                f'AuditLog: failed to pre-fetch object for {path}: {exc}'
            )
            request._audit_old_values = None
            request._audit_instance = None

    def process_exception(self, request, exception):
        """
        Log exceptions that occur during request processing.
        """
        logger.error(
            f'AuditLog: exception during {request.method} {request.path}: '
            f'{exception.__class__.__name__}: {exception}',
            exc_info=True,
        )
        return None  # Let Django handle the exception normally


class AuditLogResponseMiddleware:
    """
    Middleware that logs successful write operations after response.
    This must be placed AFTER AuditLogMiddleware in MIDDLEWARE list.

    For update (PUT/PATCH) operations, reads the old values captured by
    AuditLogMiddleware, extracts new values from the response, and stores
    both along with a summary of changes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only log write operations on API endpoints
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response

        if request.method not in LOGGED_METHODS:
            return response

        path = request.path
        if not path.startswith('/api/'):
            return response

        # Skip certain paths
        for skip_path in SKIP_PATHS:
            if path.startswith(skip_path) or path == skip_path:
                return response

        # Only log successful operations (2xx status)
        if not (200 <= response.status_code < 300):
            return response

        try:
            from auditlog.models import AuditLog

            model_name = get_model_name(path)
            action = get_action_from_method_and_path(request.method, path)

            # Try to extract object info from response
            changes = {}
            old_values = {}
            new_values = {}
            object_repr = ''
            object_id = None

            try:
                if hasattr(response, 'data'):
                    data = response.data
                    if isinstance(data, dict):
                        # Extract object representation
                        for field in ['name', 'title', 'username', 'order_number',
                                      'employee_number', 'sku', 'code']:
                            if field in data and data[field]:
                                object_repr = str(data[field])
                                break

                        if not object_repr and 'id' in data:
                            object_repr = f'#{data["id"]}'
                            object_id = data['id']

                        # For create/update, store relevant data
                        if action in ('create', 'update') and 'id' in data:
                            object_id = data['id']

                        # For create operations, store the new values
                        if action == 'create' and data:
                            new_values = self._extract_new_values(data)

                        # For update operations, compare old vs new
                        if action == 'update':
                            old_values = getattr(request, '_audit_old_values', None) or {}
                            new_values = self._extract_new_values(data)
                            changes = compute_changes(old_values, new_values)
            except Exception:
                pass

            AuditLog.log(
                user=request.user,
                action=action,
                model_name=model_name,
                object_id=object_id,
                object_repr=object_repr,
                old_values=old_values or None,
                new_values=new_values or None,
                changes=changes or None,
                request=request,
            )
        except Exception as e:
            logger.warning(f'Failed to create audit log: {e}')

        return response

    @staticmethod
    def _extract_new_values(data):
        """
        Extract new values from the response data dict, filtering out
        non-field keys and auto-managed fields.
        """
        if not isinstance(data, dict):
            return {}

        # Keys that appear in DRF responses but are not model fields
        NON_FIELD_KEYS = {
            'url', 'api_url', 'absolute_url',
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name',
            'customer_name', 'supplier_name', 'employee_name',
            'product_name', 'department_name', 'project_name',
            'account_name', 'user_name',
            'items',  # nested reverse relations
            'entries',  # nested reverse relations
            'permissions',
            'total_value',  # computed property
            'is_low_stock',  # computed property
            'subtotal',  # order item computed field (handled separately)
        }

        new_values = {}
        for key, value in data.items():
            if key in AUTO_FIELDS:
                continue
            if key in NON_FIELD_KEYS:
                continue
            if key.endswith('_display'):  # DRF choice display fields
                continue

            # Serialize the value for safe storage
            try:
                json.dumps(value)
                new_values[key] = value
            except (TypeError, ValueError, OverflowError):
                new_values[key] = str(value)

        return new_values

    def process_exception(self, request, exception):
        """
        Log exceptions that occur during response processing.
        """
        logger.error(
            f'AuditLogResponse: exception during {request.method} '
            f'{request.path}: {exception.__class__.__name__}: {exception}',
            exc_info=True,
        )
        return None
