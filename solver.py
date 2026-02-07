def solve_schedule(required_courses, current_schedule=[]):
    # BASE CASE: If we have no more courses to pick, we've succeeded!
    if not required_courses:
        return current_schedule

    # 1. CHOOSE: Pick the first course from our "Missing" list
    target_course = required_courses[0]
    remaining_courses = required_courses[1:]

    # 2. EXPLORE: Try every available section for that course
    for section in target_course['sections']:
        # Check if this section fits in our current schedule
        if not has_global_conflict(current_schedule + [section]):
            
            # Recursive call: Try to fill the rest of the slots with this section added
            result = solve_schedule(remaining_courses, current_schedule + [section])
            
            # If the recursion eventually found a full schedule, pass it up!
            if result is not None:
                return result

    # 3. UNCHOOSE: If no sections for this course worked with our 
    # current picks, return None to trigger the "Backtrack" in the previous call.
    return None