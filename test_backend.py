"""
Quick test to verify backend is working correctly
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from orchestrator import TravelMindOrchestrator
import json

# Test with specific destination
orchestrator = TravelMindOrchestrator()

print("Testing with specific destination: Marrakech, Morocco")
print("=" * 80)

user_input = {
    "travel_style": "cultural",
    "pace": "moderate",
    "specific_destination": "Marrakech, Morocco",
    "detail_level": "medium"
}

print("\nInput:")
print(json.dumps(user_input, indent=2))
print("\nGenerating plan...")

result = orchestrator.generate_plan(user_input, detail_level="medium")

print("\n" + "=" * 80)
if result.get("status") == "success":
    dest = result.get("destination", {})
    print(f"✅ SUCCESS!")
    print(f"Destination: {dest.get('name')}, {dest.get('country')}")
    print(f"Days: {len(result.get('itinerary', []))}")
else:
    print(f"❌ ERROR: {result.get('error')}")

print("\nFull result:")
print(json.dumps(result, indent=2))
