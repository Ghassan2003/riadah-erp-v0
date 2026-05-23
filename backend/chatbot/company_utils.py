"""
Company context utilities for multi-tenancy support.
Currently returns empty context since multi-company support is not yet implemented.
"""

logger = logging.getLogger(__name__)


def get_company_context(user):
    """
    Get company context for data isolation.
    Returns empty dict since multi-company support is not yet implemented.
    When Company model is added, this will return company_id and company_name.
    """
    return {}
