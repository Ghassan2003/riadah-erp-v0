"""
Company utility functions for RIADAH ERP chatbot.
Provides data isolation and company context retrieval.

NOTE: These are placeholder functions. When a Company model is introduced
into the ERP system, update these functions to reference the actual model.
"""

import logging

logger = logging.getLogger(__name__)


def get_user_company(user):
    """
    Retrieve the company associated with the given user.

    Args:
        user: The authenticated User instance.

    Returns:
        The Company object associated with the user, or None if the user
        is not associated with any company or if no Company model exists yet.
    """
    # TODO: Replace with actual Company model lookup when available.
    # Example implementation:
    #   try:
    #       return user.company
    #   except AttributeError:
    #       return None
    #
    # Or if company is a FK on User:
    #   return getattr(user, 'company', None)

    # Check if the User model has a 'company' foreign key
    if hasattr(user, 'company_id') and user.company_id:
        try:
            return user.company
        except Exception:
            return None

    return None


def filter_by_company(queryset, company):
    """
    Filter a Django queryset by the given company for data isolation.

    Args:
        queryset: A Django queryset to filter.
        company: The Company object (or company ID) to filter by.

    Returns:
        The filtered queryset. If company is None, returns the original queryset.

    Usage:
        qs = Sales.objects.all()
        company = get_user_company(user)
        qs = filter_by_company(qs, company)
    """
    if company is None:
        return queryset

    company_id = getattr(company, 'id', company)

    # Try filtering by 'company' field
    try:
        return queryset.filter(company_id=company_id)
    except Exception:
        logger.debug(
            'Cannot filter queryset by company_id — field may not exist on this model.'
        )
        return queryset


def get_company_context(user):
    """
    Retrieve company context information for the given user.

    This context is used to:
    - Isolate data queries by company.
    - Provide personalized AI responses with company-specific information.
    - Pass to the AI service for context-aware responses.

    Args:
        user: The authenticated User instance.

    Returns:
        dict: A dictionary containing company context information.
              Returns an empty dict if no company is associated.

    Example:
        {
            'company_id': 1,
            'company_name': 'شركة ريادة للتقنية',
            'company_type': 'technology',
        }
    """
    company = get_user_company(user)

    if company is None:
        return {}

    try:
        return {
            'company_id': company.id,
            'company_name': getattr(company, 'name', ''),
            'company_type': getattr(company, 'company_type', ''),
            'company_industry': getattr(company, 'industry', ''),
        }
    except Exception as exc:
        logger.warning(
            'Error building company context for user %s: %s',
            user.username,
            str(exc),
        )
        return {}
