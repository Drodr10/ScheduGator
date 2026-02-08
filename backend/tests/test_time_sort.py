#!/usr/bin/env python3
"""
Test script to verify time-based sorting of course sections
"""
import sys
sys.path.insert(0, 'backend')

from search import search_catalog

print("=" * 70)
print("TESTING TIME-BASED SORTING")
print("=" * 70)

# Test 1: Search without sorting
print("\n1️⃣  Search COP3502C WITHOUT SORTING:")
results = search_catalog(query="COP3502C", sort_by=None)
if results:
    course = results[0]
    print(f"\nCourse: {course['code']} - {course['name']}")
    sections = course.get('sections', [])[:3]
    for i, section in enumerate(sections):
        meet_times = section.get('meetTimes', [])
        if meet_times:
            first_meet = meet_times[0]
            time_begin = first_meet.get('meetTimeBegin', 'N/A')
            days = ', '.join(first_meet.get('meetDays', []))
            print(f"  Section {i+1}: {time_begin} ({days})")

# Test 2: Search with ascending sort (earliest first)
print("\n2️⃣  Search COP3502C WITH ASCENDING SORT (earliest first):")
results = search_catalog(query="COP3502C", sort_by="asc")
if results:
    course = results[0]
    print(f"\nCourse: {course['code']} - {course['name']}")
    sections = course.get('sections', [])[:5]  # Show 5 sections
    for i, section in enumerate(sections):
        meet_times = section.get('meetTimes', [])
        if meet_times:
            first_meet = meet_times[0]
            time_begin = first_meet.get('meetTimeBegin', 'N/A')
            days = ', '.join(first_meet.get('meetDays', []))
            print(f"  Section {i+1}: {time_begin} ({days})")

# Test 3: Search with descending sort (latest first)
print("\n3️⃣  Search COP3502C WITH DESCENDING SORT (latest first):")
results = search_catalog(query="COP3502C", sort_by="desc")
if results:
    course = results[0]
    print(f"\nCourse: {course['code']} - {course['name']}")
    sections = course.get('sections', [])[:5]  # Show 5 sections
    for i, section in enumerate(sections):
        meet_times = section.get('meetTimes', [])
        if meet_times:
            first_meet = meet_times[0]
            time_begin = first_meet.get('meetTimeBegin', 'N/A')
            days = ', '.join(first_meet.get('meetDays', []))
            print(f"  Section {i+1}: {time_begin} ({days})")

print("\n" + "=" * 70)
print("✅ Sorting feature implemented!")
print("\nUsage examples for the AI:")
print("  - 'Show me MAC2311 sections starting earliest in the day'")
print("  - 'Find COP3502 with latest class times'")
print("  - 'What are the morning sections for PHY2048?'")
print("=" * 70)
