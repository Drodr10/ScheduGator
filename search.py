import json
import re

def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _dept_matches(course_dept: str, dept_query: str) -> bool:
    if not dept_query:
        return True

    norm_query = _normalize_text(dept_query)
    norm_course = _normalize_text(course_dept)

    if norm_query in norm_course or norm_course in norm_query:
        return True

    words = re.findall(r"[A-Za-z]+", course_dept)
    acronym = "".join(word[0].lower() for word in words if len(word) > 1)
    if acronym and norm_query == acronym:
        return True

    return False


def search_catalog(query=None, dept=None, min_level=None, max_level=None, is_ai=None):
    """
    Search tool for the AI Agent to query the universal_base_catalog.json.
    
    Args:
        query (str): Keyword for course code or name.
        dept (str): Department name (e.g., 'Physics').
        min_level (int): Minimum course level (e.g., 3000).
        max_level (int): Maximum course level (e.g., 4000).
        is_ai (bool): Filter for courses with the AI attribute.
        Results are capped at 10 to keep responses compact.
    """
    with open('universal_base_catalog.json', 'r') as f:
        catalog = json.load(f)

    results = []
    max_results = 10
    for course in catalog:
        # 1. Text Search (Code or Name)
        if query and query.lower() not in (course['code'] + course['name']).lower():
            continue

        # 2. Department Filter
        if dept and not _dept_matches(course.get('dept', ''), dept):
            continue

        # 3. Level Filters
        try:
            # Extract first digit of course number (e.g., '3' from 'COP3502')
            course_level = int(course['code'][3]) * 1000
            if min_level and course_level < min_level: continue
            if max_level and course_level > max_level: continue
        except (IndexError, ValueError):
            pass

        # 4. AI Attribute Filter
        if is_ai is not None:
            # Matches the 'isAI' key from your ingestion script
            if course.get('isAI', False) != is_ai:
                continue

        results.append(course)
        
        # Limit results to keep the AI's context window manageable
        if len(results) >= max_results:
            break
            
    return results