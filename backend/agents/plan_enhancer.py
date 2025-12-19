"""
Plan Enhancer Agent
Enhances, modifies, or fills gaps in user-provided travel plans
"""
from typing import Dict, Any
import os
from openai import OpenAI


class PlanEnhancerAgent:
    """
    Agent responsible for enhancing user's existing travel plans
    Takes a rough plan and adds details, optimizes timing, or modifies based on user preferences
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"
    
    def enhance(
        self,
        existing_plan: str,
        destination: str,
        constraints: Dict[str, Any],
        action: str = "enhance"
    ) -> Dict[str, Any]:
        """
        Enhance an existing travel plan
        
        Args:
            existing_plan: User's rough plan text
            destination: Destination location
            constraints: Parsed constraints (dates, budget, pace, etc.)
            action: What to do - "enhance", "modify", "fill_gaps", "optimize"
        
        Returns:
            Enhanced itinerary with details
        """
        
        # Build action-specific instructions
        action_instructions = {
            "enhance": """
                Enhance the user's plan with:
                - Specific timing for each activity (morning, afternoon, evening with approximate hours)
                - Estimated costs for activities, meals, and transportation
                - Practical tips and recommendations
                - Transportation details between locations
                - Meal suggestions near each activity
                Keep the user's original structure and activities intact.
            """,
            "modify": """
                Improve and modify the user's plan by:
                - Optimizing the order of activities for better flow
                - Suggesting better alternatives if activities don't fit well together
                - Adding or replacing activities that better match their preferences
                - Balancing the daily pace according to their preferred pace
                - Adjusting for budget constraints
            """,
            "fill_gaps": """
                Fill in the gaps in the user's plan by:
                - Adding activities for any unplanned time periods
                - Suggesting meals and restaurants for breakfast, lunch, and dinner
                - Adding transportation between activities
                - Including rest breaks and free time
                - Suggesting evening activities if days end early
            """,
            "optimize": """
                Optimize the user's plan by:
                - Reorganizing activities to minimize travel time and backtracking
                - Grouping nearby attractions together
                - Adjusting timing to avoid crowds when possible
                - Ensuring realistic time allocations for each activity
                - Balancing energy levels throughout each day
            """
        }
        
        # Extract key constraint information
        dates = constraints.get('constraints', {}).get('dates', 'Not specified')
        budget = constraints.get('constraints', {}).get('budget', 'Not specified')
        pace = constraints.get('constraints', {}).get('pace', 'moderate')
        interests = constraints.get('constraints', {}).get('interests', [])
        travel_style = constraints.get('constraints', {}).get('travel_style', 'Not specified')
        group_type = constraints.get('constraints', {}).get('group_type', 'Not specified')
        
        pace_descriptions = {
            'relaxed': 'Relaxed pace - plenty of downtime, 2-3 activities per day',
            'moderate': 'Moderate pace - balanced itinerary, 3-4 activities per day',
            'packed': 'Packed schedule - maximize experiences, 5+ activities per day'
        }
        
        prompt = f"""You are an expert travel planner helping to enhance a traveler's existing plan for {destination}.

USER'S EXISTING PLAN:
{existing_plan}

TRAVEL DETAILS:
- Destination: {destination}
- Dates: {dates}
- Budget: ${budget} total (if specified)
- Pace: {pace_descriptions.get(pace, pace)}
- Travel Style: {travel_style}
- Group Type: {group_type}
- Interests: {', '.join(interests) if interests else 'General sightseeing'}

ACTION REQUESTED: {action.upper()}
{action_instructions.get(action, action_instructions['enhance'])}

IMPORTANT GUIDELINES:
1. Maintain respect for the user's original ideas and preferences
2. Provide SPECIFIC details: exact timing, actual costs, real names for resorts/restaurants
3. For ACCOMMODATION/CHECK-IN activities: include 2-3 specific luxury resort examples with names, prices, and amenities
4. For DINING activities: include 2-3 specific restaurant recommendations with cuisine type and price range
5. Include practical information: opening hours, booking requirements, dress codes
6. Consider logistics: walking distances, transportation time, bathroom breaks
7. Add insider tips and local recommendations
8. Be realistic about time - account for waiting, meals, rest
9. Format the itinerary in a clear, day-by-day structure
10. For each day include: Morning, Afternoon, Evening sections
11. For each activity provide: Name, Time, Duration, Cost, Description, Tips
12. Include 3-5 hotel recommendations with price ranges and locations at the top level
13. DO include official website links and credible sources where helpful
14. DO NOT include phone numbers or reservation contacts
15. Only include real, existing websites - avoid generating fake URLs

Respond with a well-structured enhanced itinerary in JSON format:
{{
    "destination": "{destination}",
    "overview": "Brief overview of the enhanced plan (2-3 sentences)",
    "enhancements_summary": "What was improved/added (2-3 sentences)",
    "total_estimated_cost": numeric value or null,
    "hotel_recommendations": [
        {{
            "name": "Hotel Name",
            "category": "Budget|Mid-Range|Luxury",
            "price_range": "$100-150 per night",
            "location": "Neighborhood/Area",
            "description": "Brief description of hotel and amenities",
            "best_for": "Families|Couples|Solo travelers|etc"
        }}
    ],
    "itinerary": [
        {{
            "day": 1,
            "date": "Day description or date if known",
            "theme": "Daily theme (e.g., 'Historic Center Exploration')",
            "activities": [
                {{
                    "time": "9:00 AM - 11:00 AM",
                    "name": "Activity name",
                    "type": "sightseeing|dining|transport|experience|rest",
                    "description": "Detailed description",
                    "location": "Specific address or area",
                    "duration": "Duration in minutes",
                    "cost": "Estimated cost in USD or 'Free'",
                    "tips": "Practical tips and recommendations",
                    "booking_required": true/false,
                    "priority": "must-see|recommended|optional",
                    "resort_examples": [
                        {{
                            "name": "Specific Resort/Hotel Name",
                            "category": "Luxury|Upscale",
                            "price_per_night": "$300-500",
                            "amenities": "Spa, fine dining, mountain views, etc"
                        }}
                    ],
                    "restaurant_options": [
                        {{
                            "name": "Restaurant Name",
                            "cuisine": "Italian|French|Local|etc",
                            "price_range": "$$-$$$",
                            "specialties": "Brief description of what they're known for"
                        }}
                    ]
                }}
            ],
            "daily_cost": "Estimated total for the day",
            "notes": "Any important daily notes"
        }}
    ],
    "pacing_notes": "Notes about the overall pace and energy distribution",
    "practical_tips": [
        "Important practical tip 1",
        "Important practical tip 2"
    ]
}}

Respond with ONLY the JSON, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert travel planner who enhances and improves travel itineraries with detailed, practical information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            
            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            # Add metadata
            result['action_performed'] = action
            result['original_plan'] = existing_plan
            result['status'] = 'success'
            
            return result
            
        except json.JSONDecodeError as e:
            # Fallback: create structured response from text
            return {
                "status": "success",
                "destination": destination,
                "overview": "Enhanced itinerary based on your plan",
                "enhancements_summary": f"Applied {action} to your travel plan",
                "itinerary": self._create_basic_structure(existing_plan, destination),
                "pacing_notes": f"Itinerary enhanced with {pace} pace in mind",
                "practical_tips": ["Check opening hours before visiting", "Book popular attractions in advance"],
                "action_performed": action,
                "original_plan": existing_plan,
                "parse_note": "Structured format created from AI response"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to enhance plan"
            }
    
    def _create_basic_structure(self, existing_plan: str, destination: str) -> list:
        """
        Create a basic itinerary structure from text
        Fallback when JSON parsing fails
        """
        lines = existing_plan.split('\n')
        itinerary = []
        current_day = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect day markers
            if 'day' in line.lower() and any(char.isdigit() for char in line):
                if current_day:
                    itinerary.append(current_day)
                
                day_num = ''.join(filter(str.isdigit, line))
                current_day = {
                    "day": int(day_num) if day_num else len(itinerary) + 1,
                    "date": line,
                    "theme": "As planned",
                    "activities": [],
                    "notes": ""
                }
            elif current_day:
                # Add as activity
                current_day["activities"].append({
                    "time": "See plan",
                    "name": line[:100],
                    "description": line,
                    "type": "planned_activity"
                })
        
        if current_day:
            itinerary.append(current_day)
        
        return itinerary if itinerary else [{
            "day": 1,
            "date": "Day 1",
            "theme": "Your itinerary",
            "activities": [{
                "name": "Your planned activities",
                "description": existing_plan[:500],
                "type": "planned_activity"
            }]
        }]
