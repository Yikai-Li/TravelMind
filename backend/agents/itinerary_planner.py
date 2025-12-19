"""
Itinerary Planning Agent
Generates day-by-day plan structure
"""
from typing import Dict, Any, List
from utils import call_llm, parse_json_response


class ItineraryPlannerAgent:
    """
    Agent responsible for creating day-by-day itinerary structure
    """
    
    def __init__(self):
        self.system_prompt = """You are an itinerary planning agent for a travel planning system.
Your job is to create a structured day-by-day itinerary for a chosen destination.

For each day, provide:
- day_number: Day number (1, 2, 3...)
- title: Brief day title (e.g., "Arrival & City Orientation")
- theme: Main theme or focus of the day
- activities: List of 3-5 activities with:
  - name: Activity name
  - duration: Estimated duration
  - type: Activity type (sightseeing, dining, adventure, relaxation, etc.)
  - priority: high, medium, or low
- notes: Any important notes about the day
- flexibility: How flexible this day is (rigid, moderate, flexible)

Consider:
- Logical flow and geographic clustering
- Energy levels (don't pack too much early mornings after arrival)
- Meal times and dining experiences
- Travel/transport time between activities
- Mix of must-see attractions and hidden gems
- Balance between structured activities and free time
- Pace preference (relaxed, moderate, packed)

Return response as valid JSON with this structure:
{
  "itinerary": [
    {
      "day_number": 1,
      "title": "...",
      "theme": "...",
      "activities": [
        {
          "name": "...",
          "duration": "2 hours",
          "type": "...",
          "priority": "high"
        }
      ],
      "notes": "...",
      "flexibility": "moderate"
    }
  ],
  "overview": "Brief overview of the itinerary approach",
  "pacing_notes": "Notes about overall pacing"
}"""
    
    def plan(self, destination: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create itinerary for destination
        """
        try:
            # Format prompt
            user_prompt = self._format_prompt(destination, constraints)
            
            # Call LLM
            response = call_llm(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            # Parse response
            result = parse_json_response(response)
            
            # Validate and enrich
            result = self._validate_itinerary(result, constraints)
            
            return result
            
        except Exception as e:
            return self._fallback_itinerary(destination, constraints, str(e))
    
    def _format_prompt(self, destination: Dict[str, Any], constraints: Dict[str, Any]) -> str:
        """Format prompt for itinerary planning"""
        dest_name = destination.get("name", "Unknown")
        duration = constraints.get("duration", 7)
        pace = constraints.get("constraints", {}).get("pace", "moderate")
        interests = constraints.get("constraints", {}).get("interests", [])
        travel_style = constraints.get("constraints", {}).get("travel_style", "cultural")
        group_type = constraints.get("constraints", {}).get("group_type", "solo")
        
        highlights = destination.get("highlights", [])
        
        return f"""Create a detailed {duration}-day itinerary for {dest_name}.

Destination Highlights: {', '.join(highlights)}

Traveler Profile:
- Pace: {pace}
- Travel Style: {travel_style}
- Interests: {', '.join(interests) if interests else 'General'}
- Group Type: {group_type}

Special Considerations:
{destination.get('considerations', 'None')}

Budget Category: {constraints.get('budget_category', 'moderate')}
Daily Budget: ${constraints.get('daily_budget', 0)}

Create a balanced itinerary that maximizes the experience while respecting the traveler's preferences and constraints."""
    
    def _validate_itinerary(self, result: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enrich itinerary
        """
        itinerary = result.get("itinerary", [])
        duration = constraints.get("duration", 7)
        
        # Ensure correct number of days
        if len(itinerary) != duration:
            result["warnings"] = result.get("warnings", [])
            result["warnings"].append(f"Expected {duration} days, got {len(itinerary)}")
        
        # Add day metadata
        for day in itinerary:
            activities = day.get("activities", [])
            day["activity_count"] = len(activities)
            day["high_priority_count"] = sum(1 for a in activities if a.get("priority") == "high")
            
            # Calculate estimated time
            total_hours = 0
            for activity in activities:
                duration_str = activity.get("duration", "1 hour")
                # Simple parsing
                if "hour" in duration_str:
                    try:
                        hours = float(duration_str.split()[0])
                        total_hours += hours
                    except:
                        total_hours += 1
            
            day["estimated_hours"] = total_hours
            
            # Flag overpacked days
            if total_hours > 12:
                day["packing_warning"] = "Day may be too packed"
        
        return result
    
    def _fallback_itinerary(self, destination: Dict[str, Any], constraints: Dict[str, Any], error: str) -> Dict[str, Any]:
        """
        Provide basic fallback itinerary
        """
        duration = constraints.get("duration", 7)
        dest_name = destination.get("name", "destination")
        
        itinerary = []
        for i in range(1, min(duration + 1, 8)):  # Max 7 days fallback
            if i == 1:
                day = {
                    "day_number": i,
                    "title": "Arrival & Orientation",
                    "theme": "Getting settled",
                    "activities": [
                        {"name": "Check-in to accommodation", "duration": "1 hour", "type": "logistics", "priority": "high"},
                        {"name": "Explore neighborhood", "duration": "2 hours", "type": "exploration", "priority": "medium"},
                        {"name": "Welcome dinner", "duration": "2 hours", "type": "dining", "priority": "medium"}
                    ],
                    "notes": "Take it easy on arrival day",
                    "flexibility": "flexible"
                }
            elif i == duration:
                day = {
                    "day_number": i,
                    "title": "Departure Day",
                    "theme": "Last moments",
                    "activities": [
                        {"name": "Final exploration or souvenir shopping", "duration": "2 hours", "type": "shopping", "priority": "low"},
                        {"name": "Check-out and departure", "duration": "2 hours", "type": "logistics", "priority": "high"}
                    ],
                    "notes": "Leave time for travel to airport",
                    "flexibility": "rigid"
                }
            else:
                day = {
                    "day_number": i,
                    "title": f"Exploring {dest_name} - Day {i}",
                    "theme": "Main attractions",
                    "activities": [
                        {"name": "Morning activity", "duration": "3 hours", "type": "sightseeing", "priority": "high"},
                        {"name": "Lunch", "duration": "1.5 hours", "type": "dining", "priority": "medium"},
                        {"name": "Afternoon activity", "duration": "3 hours", "type": "sightseeing", "priority": "high"},
                        {"name": "Evening experience", "duration": "2 hours", "type": "cultural", "priority": "medium"}
                    ],
                    "notes": "Full day of exploration",
                    "flexibility": "moderate"
                }
            
            itinerary.append(day)
        
        return {
            "itinerary": itinerary,
            "overview": f"Basic {duration}-day itinerary for {dest_name}",
            "pacing_notes": "Moderate pacing with flexibility",
            "fallback_mode": True,
            "error": error
        }
