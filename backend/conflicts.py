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
def has_global_conflict(sections_list):
    # Map evening periods to continue the sequence (11 -> 12, 13, 14)
    period_map = {
        "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
        "7": 7, "8": 8, "9": 9, "10": 10, "11": 11,
        "E1": 12, "E2": 13, "E3": 14
    }

    # Include 'S' just in case a lab or online exam has a Saturday slot
    daily_slots = {day: [] for day in ["M", "T", "W", "R", "F", "S"]}

    for section in sections_list:
        for time_slot in section.get('meetTimes', []):
            # Use .get() and the map to safely handle 'E' strings
            try:
                start = period_map.get(str(time_slot['meetPeriodBegin']))
                end = period_map.get(str(time_slot['meetPeriodEnd']))
            except KeyError:
                continue # Skip TBA or irregular times

            if start is None or end is None:
                continue

            for day in time_slot['meetDays']:
                # Compare against current day's commitments
                for existing_start, existing_end in daily_slots.get(day, []):
                    # Logic: If (Start_A <= End_B) AND (End_A >= Start_B), they overlap
                    if max(start, existing_start) <= min(end, existing_end):
                        return True

                daily_slots[day].append((start, end))

    return False
def check_dependencies(current_schedule, major_metadata, student_completed):
    """
    Analyzes the schedule based on the tri-state 'is_standalone_ok' field.
    """
    hard_conflicts = []
    soft_warnings = []

    # Get all codes currently in the 'cart'
    current_codes = [s['course_code'] for s in current_schedule]

    for section in current_schedule:
        code = section['course_code']
        metadata = major_metadata.get(code, {})

        policy = metadata.get('is_standalone_ok', True)
        links = metadata.get('required_links', [])

        for link in links:
            # Check if student already has credit OR has it in their current cart
            if link not in student_completed and link not in current_codes:

                if policy == False:
                    # HARD CONFLICT: Block the schedule
                    hard_conflicts.append(f"❌ {code} requires {link} to be taken concurrently.")

                elif policy == "partially":
                    # SOFT WARNING: Just a tip for the student
                    soft_warnings.append(f"💡 Tip: It's highly recommended to pair {code} with {link}.")

    return hard_conflicts, soft_warnings
