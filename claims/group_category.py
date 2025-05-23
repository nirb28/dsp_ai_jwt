import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_category(user_groups: List[str], lookup_mode: str = 'FIRST_MATCH', **kwargs) -> Dict[str, Any]:
    """
    Assign user to a category based on group membership and lookup mode.
    
    Args:
        user_groups: List of groups the user belongs to
        lookup_mode: 'FIRST_MATCH', 'ALL_MATCHES', or 'TIERED_MATCH'
        metadata: (kwarg) metadata dictionary containing 'categories'
    Returns:
        Dict with category assignment result
    """
    logger.info(f"Assigning user category for groups: {user_groups} with mode: {lookup_mode}")
    metadata = kwargs.get('metadata', {})
    categories = metadata.get('categories', {})
    if not categories:
        logger.warning("No categories found in metadata")
        return {"categories": [], "match_mode": lookup_mode, "reason": "No categories in metadata"}

    matches = []
    for cat_name, cat_data in categories.items():
        cat_groups = cat_data.get('groups', [])
        # If any group matches, consider this category
        if any(g in user_groups for g in cat_groups):
            matches.append({"name": cat_name, **cat_data})

    if lookup_mode == 'FIRST_MATCH':
        if matches:
            return {"category": matches[0], "match_mode": lookup_mode}
        else:
            return {"category": None, "match_mode": lookup_mode, "reason": "No match"}
    elif lookup_mode == 'ALL_MATCHES':
        return {"categories": matches, "match_mode": lookup_mode}
    elif lookup_mode == 'TIERED_MATCH':
        # Assume each category has a 'tier' field for ranking (higher is better)
        if matches:
            best = max(matches, key=lambda x: x.get('tier', 0))
            return {"category": best, "match_mode": lookup_mode}
        else:
            return {"category": None, "match_mode": lookup_mode, "reason": "No match"}
    else:
        logger.warning(f"Unknown lookup_mode: {lookup_mode}")
        return {"categories": matches, "match_mode": lookup_mode, "reason": "Unknown lookup_mode"}
