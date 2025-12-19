"""
Detail Enrichment Agent
Adds activity descriptions, timing, transport, and tips
"""
from typing import Dict, Any, List
from utils import call_llm, parse_json_response


class DetailEnricherAgent:
    """
    Agent responsible for enriching itinerary with detailed information
    """
    
    def __init__(self):
        self.system_prompt = """You are a detail enrichment agent for a travel planning system.
Your job is to add rich details to itinerary activities.

For each activity, provide:
- description: Detailed 2-3 sentence description
- time_slot: Suggested time (e.g., "9:00 AM - 11:00 AM")
- location: Specific location/address
- cost_estimate: Estimated cost in USD
- booking_info: Whether booking is needed (required, recommended, not_needed)
- transport_notes: How to get there from previous location
- tips: 2-3 insider tips or important notes
- alternatives: 1-2 alternative options if this doesn't work out

Also provide:
- dining_suggestions: Specific restaurant/cafe recommendations for meals
- transport_summary: Daily transportation overview
- budget_breakdown: Estimated daily costs

Return response as valid JSON maintaining the original structure but with enriched details."""
    
    def enrich(self, itinerary_data: Dict[str, Any], destination: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich itinerary with detailed information
        """
        try:
            # Process day by day to avoid context length issues
            enriched_itinerary = []
            
            for day in itinerary_data.get("itinerary", []):
                enriched_day = self._enrich_day(day, destination, constraints)
                enriched_itinerary.append(enriched_day)
            
            return {
                "itinerary": enriched_itinerary,
                "overview": itinerary_data.get("overview", ""),
                "pacing_notes": itinerary_data.get("pacing_notes", ""),
                "enrichment_level": "detailed"
            }
            
        except Exception as e:
            # Return original itinerary with basic enrichment
            return self._basic_enrichment(itinerary_data, str(e))
    
    def _enrich_day(self, day: Dict[str, Any], destination: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single day with details
        """
        try:
            user_prompt = f"""Enrich the following day of itinerary with detailed information:

Destination: {destination.get('name', 'Unknown')}
Day {day.get('day_number')}: {day.get('title')}
Theme: {day.get('theme')}

Activities:
{self._format_activities(day.get('activities', []))}

Budget: ${constraints.get('daily_budget', 100)}/day
Group Type: {constraints.get('constraints', {}).get('group_type', 'solo')}

Provide detailed information for each activity including timing, costs, transport, and tips."""
            
            response = call_llm(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.6
            )
            
            enriched = parse_json_response(response)
            
            # Merge with original day data
            result = day.copy()
            
            # Update activities with enriched data
            if "activities" in enriched:
                original_activities = day.get("activities", [])
                enriched_activities = enriched.get("activities", [])
                
                for i, orig_act in enumerate(original_activities):
                    if i < len(enriched_activities):
                        orig_act.update(enriched_activities[i])
                
                result["activities"] = original_activities
            
            # Add additional enrichment data
            if "dining_suggestions" in enriched:
                result["dining_suggestions"] = enriched["dining_suggestions"]
            if "transport_summary" in enriched:
                result["transport_summary"] = enriched["transport_summary"]
            if "budget_breakdown" in enriched:
                result["budget_breakdown"] = enriched["budget_breakdown"]
            
            return result
            
        except Exception as e:
            # Return original day with minimal enrichment
            return self._basic_day_enrichment(day)
    
    def _format_activities(self, activities: List[Dict[str, Any]]) -> str:
        """Format activities for prompt"""
        lines = []
        for i, act in enumerate(activities, 1):
            lines.append(f"{i}. {act.get('name')} ({act.get('duration')}) - {act.get('type')}")
        return "\n".join(lines)
    
    def _basic_enrichment(self, itinerary_data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """
        Provide basic enrichment on error
        """
        itinerary = itinerary_data.get("itinerary", [])
        
        for day in itinerary:
            day = self._basic_day_enrichment(day)
        
        return {
            "itinerary": itinerary,
            "overview": itinerary_data.get("overview", ""),
            "pacing_notes": itinerary_data.get("pacing_notes", ""),
            "enrichment_level": "basic",
            "error": error
        }
    
    def _basic_day_enrichment(self, day: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add basic enrichment to a day
        """
        activities = day.get("activities", [])
        current_time = 9  # Start at 9 AM
        
        for activity in activities:
            # Add basic time slots
            duration_str = activity.get("duration", "2 hours")
            hours = 2  # default
            try:
                hours = float(duration_str.split()[0])
            except:
                pass
            
            end_time = current_time + hours
            activity["time_slot"] = f"{int(current_time)}:00 - {int(end_time)}:00"
            current_time = end_time
            
            # Add basic cost estimates
            activity_type = activity.get("type", "")
            if activity_type == "dining":
                activity["cost_estimate"] = 25
            elif activity_type in ["sightseeing", "cultural"]:
                activity["cost_estimate"] = 15
            elif activity_type == "adventure":
                activity["cost_estimate"] = 50
            else:
                activity["cost_estimate"] = 10
            
            # Add basic booking info
            if activity.get("priority") == "high":
                activity["booking_info"] = "recommended"
            else:
                activity["booking_info"] = "not_needed"
            
            activity["description"] = f"Enjoy {activity.get('name')} - a {activity_type} experience."
            activity["tips"] = ["Check opening hours", "Arrive early to avoid crowds"]
        
        day["budget_breakdown"] = {
            "activities": sum(a.get("cost_estimate", 0) for a in activities),
            "meals": 40,
            "transport": 15,
            "total": sum(a.get("cost_estimate", 0) for a in activities) + 55
        }
        
        return day
