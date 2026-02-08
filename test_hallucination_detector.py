#!/usr/bin/env python3
"""
Test script to verify hallucination detection patterns
"""
import re

# Hallucination patterns
hallucination_patterns = [
    r'\d{1,2}:\d{2}\s*[AP]M',  # Times like "8:30 AM"
    r'Section\s+\d+:',  # Section listings
    r'Hall\s+\d+',  # Building/room numbers like "Hall 101"
    r'[A-Z]{3}\d{4}[A-Z]?:\s+[MTWRF]',  # Course codes with schedules
]

# Test cases
test_responses = [
    {
        "text": "MAC2311: MWF 8:30-9:20 AM (Little Hall 101)",
        "should_detect": True,
        "reason": "Contains time, building, and course schedule"
    },
    {
        "text": "Section 1: TR 9:35-10:25 AM (Bryant Hall 101)",
        "should_detect": True,
        "reason": "Contains section number, time, and building"
    },
    {
        "text": "Here are your critical tracking courses for CPS: MAC2311, PHY2048, ENC2256, COP3502C",
        "should_detect": False,
        "reason": "Just lists course codes without specific data"
    },
    {
        "text": "I can help you find those courses. Let me search for them.",
        "should_detect": False,
        "reason": "Generic response, no specific data"
    },
    {
        "text": "COP3502C: TR 10:40-12:50 PM (Marston Science Library 121)",
        "should_detect": True,
        "reason": "Contains course code with schedule and building"
    },
]

print("=" * 70)
print("HALLUCINATION DETECTION TEST")
print("=" * 70)

for i, test in enumerate(test_responses, 1):
    text = test["text"]
    should_detect = test["should_detect"]
    reason = test["reason"]
    
    # Check if any pattern matches
    detected = any(re.search(pattern, text, re.IGNORECASE) for pattern in hallucination_patterns)
    
    status = "✅" if detected == should_detect else "❌"
    print(f"\n{status} Test {i}: {'PASS' if detected == should_detect else 'FAIL'}")
    print(f"   Text: {text}")
    print(f"   Expected: {'DETECT' if should_detect else 'NO DETECT'}")
    print(f"   Actual: {'DETECT' if detected else 'NO DETECT'}")
    print(f"   Reason: {reason}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
passed = sum(1 for test in test_responses if (any(re.search(p, test["text"], re.IGNORECASE) for p in hallucination_patterns)) == test["should_detect"])
print(f"✅ Passed: {passed}/{len(test_responses)}")
print(f"❌ Failed: {len(test_responses) - passed}/{len(test_responses)}")
print("=" * 70)
