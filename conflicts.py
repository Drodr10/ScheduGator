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
