import json
import os
import re

def _normalize_text(value: str) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _time_to_minutes(time_str):
    """Convert time string like '8:30 AM' or period number to minutes since midnight."""
    if isinstance(time_str, int):
        # Period numbers (1-13 for UF): approximate conversion
        # Period 1 starts at 7:25 AM, each period is ~55 min apart
        return 445 + (time_str - 1) * 55
    
    if isinstance(time_str, str):
        # Handle format like "8:30 AM" or "08:30 AM"
        time_str = time_str.strip().upper()
        try:
            if 'AM' in time_str or 'PM' in time_str:
                is_pm = 'PM' in time_str
                time_part = time_str.replace('AM', '').replace('PM', '').strip()
                
                if ':' in time_part:
                    hour, minute = time_part.split(':')
                    hour = int(hour)
                    minute = int(minute)
                else:
                    hour = int(time_part)
                    minute = 0
                
                # Convert to 24-hour format
                if is_pm and hour != 12:
                    hour += 12
                elif not is_pm and hour == 12:
                    hour = 0
                
                return hour * 60 + minute
        except (ValueError, AttributeError):
            pass
    
    return 999999  # Return large value for invalid times (sorts to end)


def _get_earliest_time(section):
    """Extract the earliest meeting time from a section."""
    meet_times = section.get('meetTimes', [])
    if not meet_times:
        return 999999  # Sections without times sort to end
    
    earliest = 999999
    for meet_time in meet_times:
        # Prefer meetTimeBegin (actual time like "10:40 AM")
        begin = meet_time.get('meetTimeBegin')
        if not begin:
            # Fallback to meetPeriodBegin if meetTimeBegin not available
            begin = meet_time.get('meetPeriodBegin')
        
        if begin:
            minutes = _time_to_minutes(begin)
            earliest = min(earliest, minutes)
    
    return earliest


def _dept_matches(course_dept: str, dept_query: str) -> bool:
    if not dept_query:
        return True

    # Convert to strings to handle any type
    course_dept = str(course_dept) if course_dept else ""
    dept_query = str(dept_query) if dept_query else ""

    norm_query = _normalize_text(dept_query)
    norm_course = _normalize_text(course_dept)

    if norm_query in norm_course or norm_course in norm_query:
        return True

    # Check acronym match (e.g., CISE)
    words = re.findall(r"[A-Za-z]+", course_dept)
    acronym = "".join(word[0].lower() for word in words if len(word) > 1)
    if acronym and norm_query == acronym:
        return True

    return False


def search_catalog(query=None, queries=None, dept=None, min_level=1000, max_level=7000, is_ai=None, sort_by=None):
    """
    Search tool for the AI Agent to query the universal_base_catalog.json.
    
    Args:
        query (str): Keyword for course code or name.
        queries (list): List of keywords to search (e.g., ["COP", "CIS"]) - returns results matching ANY of them.
        dept (str): Department name (e.g., 'Physics').
        min_level (int): Minimum course level (e.g., 3000).
        max_level (int): Maximum course level (e.g., 4000).
        is_ai (bool): Filter for courses with the AI attribute.
        sort_by (str): Sort sections by time - 'asc' (earliest first), 'desc' (latest first), or None.
        Results are capped at 10 to keep responses compact.
    """
    # Get the path relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    catalog_path = os.path.join(current_dir, '..', 'data', 'universal_base_catalog.json')
    
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)

    results = []
    max_results = 10
    for course in catalog:
        # 1. Text Search (Code or Name)
        if query:
            query_str = str(query).lower()
            code_lower = course['code'].lower()
            name_lower = course['name'].lower()
            # Check if query is a prefix of the course code, or if it appears as a standalone word in name
            if not (code_lower.startswith(query_str) or query_str in name_lower.split()):
                continue
        elif queries:
            # If queries list is provided, match ANY of them
            match_found = False
            for q in queries:
                q_str = str(q).lower()
                code_lower = course['code'].lower()
                name_lower = course['name'].lower()
                # Check if q is a prefix of the course code, or if it appears as a standalone word in name
                if code_lower.startswith(q_str) or q_str in name_lower.split():
                    match_found = True
                    break
            if not match_found:
                continue
        # If neither query nor queries provided, don't filter by query

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

        # Sort sections by time if requested
        if sort_by and 'sections' in course:
            sections = course.get('sections', [])
            if sections:
                reverse = (str(sort_by).lower() == 'desc')
                sorted_sections = sorted(sections, key=_get_earliest_time, reverse=reverse)
                course = {**course, 'sections': sorted_sections}
        
        results.append(course)
        
        # Limit results to keep the AI's context window manageable
        if len(results) >= max_results:
            break
            
    return results