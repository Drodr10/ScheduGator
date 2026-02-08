#!/usr/bin/env python3
"""Test the new add_course_tool"""

from backend.brain import GemmaBrain
import json

brain = GemmaBrain()

# Test with a known classNum from the catalog (e.g., 10091 from ABE3000C)
print("Testing add_course_tool with classNum=10091...")
result = brain.add_course_tool(classNum=10091)

print("\nResult:")
print(json.dumps(result, indent=2))

if result.get("status") == "success":
    print("\n✅ Test passed! Found course:")
    course = result.get("course")
    if course:
        print(f"  Code: {course['code']}")
        print(f"  Name: {course['name']}")
        print(f"  ClassNum: {course['classNum']}")
        print(f"  Instructors: {', '.join(course['instructors'])}")
        print(f"  Credits: {course['credits']}")
else:
    print(f"\n❌ Test failed: {result.get('message')}")
