"""
TravelMind Demo Script
Demonstrates the travel planning system with example requests
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import TravelMindOrchestrator
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_high_level_recommendations():
    """Demo: Get high-level destination recommendations"""
    print_section("Demo 1: High-Level Destination Recommendations")
    
    orchestrator = TravelMindOrchestrator()
    
    # Minimal input - let the AI fill in the gaps
    user_input = {
        "travel_style": "adventure",
        "budget": 3000,
        "interests": ["hiking", "nature"]
    }
    
    print("User Input:")
    print(json.dumps(user_input, indent=2))
    print("\nGenerating recommendations...\n")
    
    result = orchestrator.generate_plan(
        user_input=user_input,
        detail_level="high_level",
        debug_mode=False
    )
    
    if result.get("status") == "success":
        print(f"✅ Success! Generated {len(result.get('destinations', []))} recommendations\n")
        
        for i, dest in enumerate(result.get('destinations', []), 1):
            print(f"{i}. {dest['name']}, {dest['country']} (Score: {dest['score']}/100)")
            print(f"   Best for: {dest.get('best_for', 'N/A')}")
            print(f"   Daily cost: ${dest.get('estimated_daily_cost', 0)}")
            print()
    else:
        print(f"❌ Error: {result.get('error')}")


def demo_full_itinerary():
    """Demo: Generate a full detailed itinerary"""
    print_section("Demo 2: Full Detailed Itinerary")
    
    orchestrator = TravelMindOrchestrator()
    
    # Rich input for detailed planning
    user_input = {
        "dates": "2024-07-01 to 2024-07-07",
        "departure_city": "Los Angeles",
        "budget": 2500,
        "travel_style": "cultural",
        "interests": ["museums", "local food", "architecture"],
        "pace": "moderate",
        "group_type": "couple"
    }
    
    print("User Input:")
    print(json.dumps(user_input, indent=2))
    print("\nGenerating full itinerary (this may take a moment)...\n")
    
    result = orchestrator.generate_plan(
        user_input=user_input,
        detail_level="full",
        debug_mode=False
    )
    
    if result.get("status") == "success":
        print(f"✅ Success! Created {len(result.get('itinerary', []))}-day itinerary")
        print(f"   Destination: {result.get('destination', {}).get('name')}")
        print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
        print(f"   Plan ID: {result.get('plan_id')}\n")
        
        # Show first day as example
        if result.get('itinerary'):
            first_day = result['itinerary'][0]
            print(f"Day 1 Preview: {first_day.get('title')}")
            print(f"Theme: {first_day.get('theme')}")
            print(f"Activities: {len(first_day.get('activities', []))}")
            
            if first_day.get('activities'):
                print("\nFirst activity:")
                act = first_day['activities'][0]
                print(f"  - {act.get('name')} ({act.get('duration')})")
                print(f"    Type: {act.get('type')}, Priority: {act.get('priority')}")
    else:
        print(f"❌ Error: {result.get('error')}")


def demo_minimal_input():
    """Demo: Minimal input to show progressive disclosure"""
    print_section("Demo 3: Progressive Disclosure - Minimal Input")
    
    orchestrator = TravelMindOrchestrator()
    
    # Very minimal input
    user_input = {
        "travel_style": "relaxation"
    }
    
    print("User Input (minimal):")
    print(json.dumps(user_input, indent=2))
    print("\nGenerating plan with assumptions...\n")
    
    result = orchestrator.generate_plan(
        user_input=user_input,
        detail_level="medium",
        debug_mode=False
    )
    
    if result.get("status") == "success":
        print(f"✅ Success!")
        
        if result.get('assumptions'):
            print("\nAssumptions made:")
            for assumption in result['assumptions']:
                print(f"  • {assumption}")
        
        if result.get('warnings'):
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning}")
    else:
        print(f"❌ Error: {result.get('error')}")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  🌍 TravelMind Demo - AI-Powered Travel Planning")
    print("=" * 80)
    
    print("\nThis demo showcases TravelMind's capabilities:")
    print("  1. High-level destination recommendations")
    print("  2. Full detailed itinerary generation")
    print("  3. Progressive disclosure with minimal input")
    
    print("\n⚠️  Note: You need to set OPENAI_API_KEY environment variable")
    print("   Example: set OPENAI_API_KEY=sk-your-key-here")
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found in environment variables")
        print("   Please set it before running the demo:")
        print("   - Windows: set OPENAI_API_KEY=your_key")
        print("   - Linux/Mac: export OPENAI_API_KEY=your_key")
        return
    
    try:
        # Run demos
        demo_high_level_recommendations()
        
        print("\n" + "-" * 80)
        input("\nPress Enter to continue to next demo...")
        
        demo_full_itinerary()
        
        print("\n" + "-" * 80)
        input("\nPress Enter to continue to next demo...")
        
        demo_minimal_input()
        
        print_section("Demo Complete!")
        print("All demos completed successfully! 🎉")
        print("\nNext steps:")
        print("  1. Start the backend: cd backend && python api.py")
        print("  2. Start the frontend: cd frontend && npm install && npm run dev")
        print("  3. Open http://localhost:3000 in your browser")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
