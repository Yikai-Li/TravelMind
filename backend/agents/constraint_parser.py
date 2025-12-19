"""
Constraint Parsing Agent
Normalizes user input into structured constraints
"""
from typing import Dict, Any, List
from utils import call_llm, parse_json_response, calculate_trip_duration, validate_budget


class ConstraintParserAgent:
    """
    Agent responsible for parsing and normalizing user input into structured constraints
    """
    
    def __init__(self):
        self.system_prompt = """You are a constraint parsing agent for a travel planning system.
Your job is to analyze user input and extract structured travel constraints.

Extract and normalize the following fields:
- dates: Travel dates in format "YYYY-MM-DD to YYYY-MM-DD"
- departure_city: City of departure
- budget: Total budget in USD (number)
- travel_style: One of [adventure, relaxation, cultural, luxury, budget, family, romantic]
- interests: List of interests/activities
- pace: One of [relaxed, moderate, packed]
- group_type: One of [solo, couple, family, friends, group]
- special_constraints: Any special requirements (mobility, dietary, etc.)
- fixed_events: Any pre-booked events or fixed schedule items

If information is missing, set it to null. Make reasonable inferences where appropriate.
Flag any conflicts or unrealistic combinations.

Return your response as valid JSON only."""
    
    def parse(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and normalize user constraints
        """
        try:
            # If input is already structured from the form, use it directly
            # Don't call LLM - it might change the values!
            parsed = user_input.copy()
            
            # Validate and enrich
            result = self._validate_and_enrich(parsed)
            
            return result
            
        except Exception as e:
            # Fallback: return input as-is with error flag
            return {
                "constraints": user_input,
                "warnings": [f"Parsing error: {str(e)}"],
                "assumptions": [],
                "conflicts": [],
                "parse_error": True
            }
    
    def _format_input(self, user_input: Dict[str, Any]) -> str:
        """Format user input for LLM"""
        return f"""Parse the following travel planning input:

{user_input}

Extract structured constraints and identify any issues."""
    
    def _validate_and_enrich(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parsed constraints and add metadata
        """
        constraints = parsed
        warnings = []
        assumptions = []
        conflicts = []
        
        # Calculate trip duration
        duration = 7  # default
        if constraints.get("dates"):
            duration = calculate_trip_duration(constraints["dates"])
            if duration < 1:
                conflicts.append("Invalid date range")
            elif duration > 30:
                warnings.append("Very long trip - may need multiple destinations")
        else:
            assumptions.append("Assuming 7-day trip")
        
        # Validate budget
        budget_info = validate_budget(constraints.get("budget"), duration)
        if budget_info.get("warnings"):
            warnings.extend(budget_info["warnings"])
        
        # Check for conflicts
        if constraints.get("travel_style") == "luxury" and budget_info.get("category") == "budget":
            conflicts.append("Luxury travel style conflicts with budget constraints")
        
        if constraints.get("pace") == "relaxed" and duration < 4:
            warnings.append("Short trip with relaxed pace - limited time per activity")
        
        # Set defaults ONLY for truly missing fields - don't override user input
        if not constraints.get("pace"):
            constraints["pace"] = "moderate"
            assumptions.append("Assuming moderate pace")
        
        # DON'T set default travel_style - user may have selected one
        # Only add if completely missing from input
        
        return {
            "constraints": constraints,
            "duration": duration,
            "budget_category": budget_info.get("category", "unspecified"),
            "daily_budget": budget_info.get("daily_budget", 0),
            "warnings": warnings,
            "assumptions": assumptions,
            "conflicts": conflicts
        }
