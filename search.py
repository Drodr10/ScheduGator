import json

def search_catalog(query=None, dept=None, min_level=None, max_level=None, is_tracking=None, is_ai=None, req_limit=15):
    """
    Search tool for the AI Agent to query the universal_base_catalog.json.
    
    Args:
        query (str): Keyword for course code or name.
        dept (str): Department name (e.g., 'Physics').
        min_level (int): Minimum course level (e.g., 3000).
        max_level (int): Maximum course level (e.g., 4000).
        is_tracking (bool): Filter for Critical Tracking courses.
        is_ai (bool): Filter for courses with the AI attribute.
        req_limit (int): Maximum number of results to return (default is 15). 
    """
    with open('universal_base_catalog.json', 'r') as f:
        catalog = json.load(f)

    results = []
    for course in catalog:
        # 1. Text Search (Code or Name)
        if query and query.lower() not in (course['code'] + course['name']).lower():
            continue

        # 2. Department Filter
        if dept and dept.lower() not in course['dept'].lower():
            continue

        # 3. Level Filters
        try:
            # Extract first digit of course number (e.g., '3' from 'COP3502')
            course_level = int(course['code'][3]) * 1000
            if min_level and course_level < min_level: continue
            if max_level and course_level > max_level: continue
        except (IndexError, ValueError):
            pass

        # 4. Critical Tracking Filter
        if is_tracking is not None:
            # Ensure course has the flag; default to False if missing
            if course.get('is_tracking', False) != is_tracking:
                continue

        # 5. AI Attribute Filter
        if is_ai is not None:
            # Matches the 'isAI' key from your ingestion script
            if course.get('isAI', False) != is_ai:
                continue

        results.append(course)
        
        # Limit results to keep the AI's context window manageable
        if len(results) >= req_limit:
            break
            
    return results