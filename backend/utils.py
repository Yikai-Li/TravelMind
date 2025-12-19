"""
Utility functions for TravelMind backend
"""
import json
import os
from typing import Any, Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    response_format: Optional[Dict[str, str]] = None,
    max_retries: int = 3
) -> str:
    """
    Call OpenAI LLM with error handling and retries
    """
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"LLM call failed after {max_retries} attempts: {str(e)}")
            continue
    
    return ""


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response from LLM with error handling
    """
    try:
        # Try to extract JSON if embedded in markdown
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        return json.loads(response)
    except json.JSONDecodeError as e:
        # Fallback: try to fix common issues
        try:
            # Remove trailing commas
            fixed = response.replace(",]", "]").replace(",}", "}")
            return json.loads(fixed)
        except:
            raise Exception(f"Failed to parse JSON response: {str(e)}")


def format_constraint_for_llm(constraints: Dict[str, Any]) -> str:
    """
    Format user constraints into readable text for LLM
    """
    parts = []
    
    if constraints.get("dates"):
        parts.append(f"Travel Dates: {constraints['dates']}")
    if constraints.get("departure_city"):
        parts.append(f"Departure City: {constraints['departure_city']}")
    if constraints.get("budget"):
        parts.append(f"Budget: ${constraints['budget']}")
    if constraints.get("travel_style"):
        parts.append(f"Travel Style: {constraints['travel_style']}")
    if constraints.get("travel_range"):
        parts.append(f"Travel Range: {constraints['travel_range']}")
    if constraints.get("interests"):
        parts.append(f"Interests: {', '.join(constraints['interests'])}")
    if constraints.get("pace"):
        parts.append(f"Pace: {constraints['pace']}")
    if constraints.get("group_type"):
        parts.append(f"Group Type: {constraints['group_type']}")
    if constraints.get("special_constraints"):
        parts.append(f"Special Constraints: {constraints['special_constraints']}")
    if constraints.get("fixed_events"):
        parts.append(f"Fixed Events: {json.dumps(constraints['fixed_events'])}")
    
    return "\n".join(parts)


def calculate_trip_duration(dates_str: str) -> int:
    """
    Calculate trip duration in days from date string
    """
    try:
        if " to " in dates_str:
            from datetime import datetime
            start, end = dates_str.split(" to ")
            start_date = datetime.strptime(start.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end.strip(), "%Y-%m-%d")
            return (end_date - start_date).days + 1
    except:
        pass
    
    # Default to 7 days if parsing fails
    return 7


def validate_budget(budget: Optional[float], duration: int) -> Dict[str, Any]:
    """
    Validate and categorize budget
    """
    if not budget or budget <= 0:
        return {
            "valid": True,
            "category": "unspecified",
            "warnings": ["Budget not specified - will provide general recommendations"]
        }
    
    daily_budget = budget / duration if duration > 0 else budget
    
    warnings = []
    if daily_budget < 50:
        warnings.append("Budget is very tight - expect basic accommodations and limited activities")
    elif daily_budget < 100:
        category = "budget"
    elif daily_budget < 300:
        category = "moderate"
    elif daily_budget < 500:
        category = "comfortable"
    else:
        category = "luxury"
    
    return {
        "valid": True,
        "category": category if not warnings else "budget",
        "daily_budget": daily_budget,
        "warnings": warnings
    }


def generate_plan_id() -> str:
    """
    Generate unique plan ID
    """
    import uuid
    return str(uuid.uuid4())[:8]


# Storage for debug traces (in production, use a database)
debug_traces = {}


def store_debug_trace(plan_id: str, trace: Dict[str, Any]):
    """
    Store debug trace for a plan
    """
    debug_traces[plan_id] = trace


def get_debug_trace(plan_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve debug trace for a plan
    """
    return debug_traces.get(plan_id)
