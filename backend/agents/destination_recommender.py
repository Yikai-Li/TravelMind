"""
Destination Recommendation Agent
Proposes and ranks suitable travel destinations
"""
from typing import Dict, Any, List
from utils import call_llm, parse_json_response, format_constraint_for_llm


class DestinationRecommenderAgent:
    """
    Agent responsible for recommending travel destinations based on constraints
    """
    
    def __init__(self):
        self.system_prompt = """You are a destination recommendation agent for a travel planning system.
Your job is to suggest DIVERSE and VARIED travel destinations based SPECIFICALLY on the user's stated preferences.

CRITICAL INSTRUCTIONS:
- ALWAYS provide different and varied destinations - never suggest the same places repeatedly
- CAREFULLY READ the user's travel style, interests, budget, and preferences
- Base recommendations DIRECTLY on what the user specified (e.g., if they want adventure and hiking, suggest mountain/nature destinations)
- If user wants cultural travel, suggest historically rich cities
- If user wants relaxation, suggest beach/resort destinations
- If user wants budget travel, suggest affordable countries
- AVOID defaulting to popular tourist destinations unless they match the user's specific interests
- Provide 5 diverse options that span different regions/countries

Consider:
- Budget and value for money (must match user's stated budget)
- Travel style and interests alignment (THIS IS MOST IMPORTANT - match their stated interests)
- Seasonality and weather for the travel dates
- Distance from departure city if specified
- Unique experiences matching their specific interests
- Variety across different regions and cultures

For EACH destination, provide:
- name: Specific destination name
- country: Country
- score: Suitability score based on how well it matches their preferences (0-100)
- reasoning: 2-3 sentences explaining WHY this destination matches their specific interests and travel style
- highlights: Top 3-5 attractions/experiences that align with their interests
- estimated_daily_cost: Realistic daily budget estimate
- best_for: What this destination excels at (related to user's interests)
- considerations: Important info (weather, visa, safety, etc.)

Return ONLY valid JSON with this exact structure:
{
  "destinations": [
    {
      "name": "Destination Name",
      "country": "Country",
      "score": 95,
      "reasoning": "Explain why this matches their travel style and interests...",
      "highlights": ["attraction 1", "attraction 2", "attraction 3"],
      "estimated_daily_cost": 150,
      "best_for": "What aligns with their interests",
      "considerations": "Important notes"
    }
  ],
  "reasoning_summary": "Brief explanation of recommendation approach"
}"""
    
    def recommend(self, parsed_constraints: Dict[str, Any], count: int = 5) -> Dict[str, Any]:
        """
        Recommend destinations based on constraints (default 5 destinations for variety)
        """
        try:
            # Format constraints
            user_prompt = self._format_prompt(parsed_constraints, count)
            
            # Print for debugging
            print(f"\n{'='*80}")
            print("DESTINATION RECOMMENDER - User Prompt:")
            print(user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt)
            print(f"{'='*80}\n")
            
            # Call LLM with higher temperature for more diverse recommendations
            response = call_llm(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,  # Slightly lower for more reliability
                model="gpt-4o-mini"  # Use reliable model
            )
            
            print(f"LLM Response received: {len(response)} characters")
            
            # Parse response
            result = parse_json_response(response)
            
            print(f"Parsed {len(result.get('destinations', []))} destinations")
            
            # Validate and enrich
            result = self._validate_recommendations(result, parsed_constraints)
            
            return result
            
        except Exception as e:
            # Log the error
            print(f"ERROR in destination_recommender: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback: return safe default recommendations
            return self._fallback_recommendations(parsed_constraints, str(e))
    
    def _format_prompt(self, parsed_constraints: Dict[str, Any], count: int) -> str:
        """Format constraints for LLM with enhanced contextual awareness"""
        constraints = parsed_constraints.get("constraints", {})
        duration = parsed_constraints.get("duration", 7)
        budget_category = parsed_constraints.get("budget_category", "moderate")
        
        constraint_text = format_constraint_for_llm(constraints)
        
        # Get key parameters for contextual recommendations
        departure_city = constraints.get("departure_city", "")
        travel_style = constraints.get("travel_style", "cultural")
        interests = constraints.get("interests", [])
        group_type = constraints.get("group_type", "solo")
        dates = constraints.get("dates", "")
        budget = constraints.get("budget", 0)
        travel_range = constraints.get("travel_range", "")
        rejected_destinations = constraints.get("rejected_destinations", [])
        additional_notes = constraints.get("additional_notes", "")
        
        # Determine season from dates
        season_hint = ""
        if dates:
            # Extract month from dates
            try:
                if "-" in dates:
                    month = int(dates.split("-")[1])
                    if month in [12, 1, 2]:
                        season_hint = "WINTER (Dec-Feb)"
                    elif month in [3, 4, 5]:
                        season_hint = "SPRING (Mar-May)"
                    elif month in [6, 7, 8]:
                        season_hint = "SUMMER (Jun-Aug)"
                    else:
                        season_hint = "FALL (Sep-Nov)"
            except:
                pass
        
        # Build contextual instructions
        context_instructions = f"""
IMPORTANT CONTEXT-BASED RECOMMENDATIONS:
"""
        
        # Add rejected destinations memory
        if rejected_destinations and len(rejected_destinations) > 0:
            context_instructions += f"""
- REJECTED DESTINATIONS (DO NOT RECOMMEND THESE):
  User has already rejected: {', '.join(rejected_destinations)}
  * DO NOT suggest these destinations again
  * Find SIMILAR but DIFFERENT alternatives
  * If user rejected a beach destination, try different beach destinations
  * If user rejected a city, try different cities with similar vibe
  * Learn from rejections to understand what user doesn't want
"""
        
        # Add user's additional notes
        if additional_notes:
            context_instructions += f"""
- USER'S ADDITIONAL PREFERENCES:
  "{additional_notes}"
  * Pay close attention to these new requirements
  * Adjust recommendations accordingly
"""
        
        if departure_city:
            # Add trip duration proximity rules
            if duration <= 3:
                proximity_rule = f"""
- Departure City: {departure_city}
- Trip Duration: SHORT ({duration} days)
- CRITICAL: Recommend ONLY nearby destinations within 2-3 hours
- Examples: 
  * Pittsburgh → Nearby state parks, Philadelphia (driveable), Cleveland
  * New York → Hamptons, Connecticut, nearby beaches (driveable/short flight)
  * Los Angeles → San Diego, Santa Barbara, Joshua Tree (driveable)
- Focus on: Minimal travel time, maximize destination time
- Avoid: Long-haul flights that waste precious vacation days
"""
            elif duration <= 7:
                proximity_rule = f"""
- Departure City: {departure_city}
- Trip Duration: MEDIUM ({duration} days)
- Recommend: Mix of nearby and regional destinations
- Examples:
  * New York → Caribbean (2-4 hour flights), Canada, Florida
  * Los Angeles → Mexico, Hawaii, Pacific Northwest
- Consider: 1-4 hour flights acceptable, but factor in airport time
- Preference: Direct flights when possible
"""
            else:
                proximity_rule = f"""
- Departure City: {departure_city}  
- Trip Duration: LONG ({duration}+ days)
- Recommend: Mix of nearby and international destinations
- Can include: Long-haul flights (Europe, Asia, etc.) as there's time
- Consider: Multi-city trips possible with longer duration
"""
            
            context_instructions += proximity_rule
        
        # Add travel range restrictions
        if travel_range:
            if travel_range == "local":
                context_instructions += f"""
- Travel Range: LOCAL (Same Region)
- Recommend ONLY: Driveable destinations, same state/province, within 2-3 hours
- NO flights required - road trip friendly
"""
            elif travel_range == "domestic":
                context_instructions += f"""
- Travel Range: DOMESTIC
- Recommend ONLY: Destinations within the same country
- NO international travel - no passport needed
"""
            elif travel_range == "regional":
                context_instructions += f"""
- Travel Range: REGIONAL (Nearby Countries)
- Recommend: Neighboring countries, short flights only
- Examples from US: Canada, Mexico, Caribbean
- Examples from Europe: Within EU/Schengen
"""
            elif travel_range == "international":
                context_instructions += f"""
- Travel Range: INTERNATIONAL
- Open to: Any destination worldwide
- Include: Long-haul flights, multiple time zones, diverse cultures
"""
        
        # Add visa awareness instruction
        context_instructions += f"""
- VISA REQUIREMENTS: 
  * ALWAYS mention visa requirements in 'considerations' field
  * If international travel from US: Note if visa is required, visa-free, or eVisa
  * Examples: "Visa required for US citizens" or "Visa-free for US passport holders" or "eVisa available online"
  * For Canada/Mexico from US: Mention passport requirements

- DISTANCE INFORMATION:
  * In the 'considerations' field, also mention approximate travel distance/time from {departure_city if departure_city else 'departure'}
  * Examples: "~2 hour drive", "~3 hour flight", "~250 miles by car"
  * This helps travelers understand accessibility
"""
        
        if travel_style == "relaxation":
            context_instructions += f"""
- Travel Style: RELAXATION
- Recommend: Beach resorts, spa destinations, peaceful retreats, island getaways
- Examples: If near coast → beach towns; If inland → mountain retreats, spa resorts
- Focus on: Calm atmospheres, wellness, beaches, nature
"""
        elif travel_style == "luxury":
            context_instructions += f"""
- Travel Style: LUXURY
- Recommend: 5-star resorts, exclusive destinations, high-end experiences
- Examples: Dubai, Monaco, Maldives, Las Vegas (casinos/shows), luxury safari, private islands
- Focus on: Michelin restaurants, luxury hotels, exclusive experiences, high-end shopping
"""
        elif travel_style == "adventure":
            context_instructions += f"""
- Travel Style: ADVENTURE
- Recommend: Mountain destinations, national parks, adventure hubs
- Examples: Patagonia, Nepal, New Zealand, Costa Rica, Iceland
- Focus on: Hiking, climbing, water sports, extreme activities
"""
        elif travel_style == "budget":
            context_instructions += f"""
- Travel Style: BUDGET
- Recommend: Affordable destinations with great value
- Examples: Southeast Asia, Eastern Europe, Central America, India
- Focus on: Low cost of living, free attractions, budget accommodations
"""
        
        if interests:
            context_instructions += f"""
- Specific Interests: {', '.join(interests)}
- MUST match these interests in recommendations
"""
        
        # Add seasonality awareness
        if season_hint:
            context_instructions += f"""
- Travel Season: {season_hint}
- CRITICAL SEASONALITY RULES:
  * WINTER → Avoid destinations where it's summer (southern hemisphere) if activities need winter
  * SUMMER → Avoid ski destinations, recommend beach/warm weather destinations
  * Match activities to season (e.g., skiing in winter, beaches in summer)
  * Consider weather appropriateness for activities
  * Don't recommend snow activities in summer or beach activities in locations experiencing winter
"""
        
        # Add group type awareness
        if group_type == "couple" and travel_style == "romantic":
            context_instructions += f"""
- Group Type: COUPLE (ROMANTIC)
- Recommend: Romantic destinations perfect for dates/honeymoons
- Examples: Paris, Santorini, Venice, Maldives, wine country, romantic cruises
- Focus on: Intimate restaurants, sunset views, couples' activities, romantic hotels
- Consider: Cruises (Caribbean, Mediterranean), wine tours, boutique hotels
"""
        elif group_type == "family":
            context_instructions += f"""
- Group Type: FAMILY
- Recommend: Family-friendly destinations with activities for all ages
- Examples: Theme parks, beach resorts with kids clubs, family-oriented cruises
- Focus on: Safety, kid-friendly activities, family accommodations
- Avoid: Party destinations, extreme adventure only
"""
        elif group_type == "friends":
            context_instructions += f"""
- Group Type: FRIENDS
- Recommend: Social destinations with nightlife and group activities
- Examples: Party cities, adventure hubs, festival destinations
- Focus on: Group activities, social scenes, shared experiences
"""
        
        # Add budget-specific guidance
        if budget and budget > 0:
            daily_budget = budget / duration if duration > 0 else budget
            context_instructions += f"""
- Total Budget: ${budget} ({duration} days = ${daily_budget:.0f}/day)
- Recommend ONLY destinations where ${daily_budget:.0f}/day is realistic
- CRITICAL: Don't recommend expensive destinations if budget is tight
- Consider: Accommodation, food, activities, transportation costs
"""
        
        return f"""Recommend {count} HIGHLY CONTEXTUAL travel destinations for this specific traveler:

{constraint_text}

Trip Duration: {duration} days
Budget Category: {budget_category}

{context_instructions}

CRITICAL: Use your knowledge of popular destinations, travel trends, and geographic proximity to make realistic, specific recommendations. Think like a knowledgeable travel agent who understands what travelers from {departure_city or 'various cities'} typically enjoy for {travel_style} trips.

Provide {count} well-matched, DIVERSE destination recommendations with detailed reasoning for each choice."""
    
    def _validate_recommendations(self, result: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enrich recommendations
        """
        destinations = result.get("destinations", [])
        
        # Check budget alignment
        daily_budget = constraints.get("daily_budget", 0)
        if daily_budget > 0:
            for dest in destinations:
                estimated = dest.get("estimated_daily_cost", 0)
                if estimated > daily_budget * 1.5:
                    dest["budget_warning"] = f"Estimated cost (${estimated}/day) exceeds budget"
                elif estimated > daily_budget:
                    dest["budget_note"] = "May need budget adjustments"
        
        # Sort by score
        destinations.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        result["destinations"] = destinations
        return result
    
    def _fallback_recommendations(self, constraints: Dict[str, Any], error: str) -> Dict[str, Any]:
        """
        Provide safe fallback recommendations on error
        """
        travel_style = constraints.get("constraints", {}).get("travel_style", "cultural")
        budget_cat = constraints.get("budget_category", "moderate")
        
        # Simple rule-based fallbacks
        fallback_dest = []
        
        if budget_cat == "budget":
            fallback_dest = [
                {
                    "name": "Mexico City",
                    "country": "Mexico",
                    "score": 85,
                    "reasoning": "Great value destination with rich culture, excellent food, and budget-friendly accommodations.",
                    "highlights": ["Historic Center", "Teotihuacan Pyramids", "Street Food", "Museums", "Xochimilco"],
                    "estimated_daily_cost": 60,
                    "best_for": "Culture, food, and history on a budget",
                    "considerations": "Altitude adjustment may be needed"
                },
                {
                    "name": "Lisbon",
                    "country": "Portugal",
                    "score": 82,
                    "reasoning": "Affordable European destination with beautiful architecture, coastline, and vibrant culture.",
                    "highlights": ["Historic Trams", "Belém Tower", "Pastéis de Nata", "Alfama District"],
                    "estimated_daily_cost": 80,
                    "best_for": "European charm on a budget",
                    "considerations": "Hilly terrain"
                }
            ]
        else:
            fallback_dest = [
                {
                    "name": "Barcelona",
                    "country": "Spain",
                    "score": 88,
                    "reasoning": "World-class destination combining culture, architecture, beaches, and cuisine.",
                    "highlights": ["Sagrada Familia", "Park Güell", "Gothic Quarter", "Beaches", "Tapas"],
                    "estimated_daily_cost": 150,
                    "best_for": "Balanced urban and beach experience",
                    "considerations": "Crowded in peak season"
                },
                {
                    "name": "Kyoto",
                    "country": "Japan",
                    "score": 86,
                    "reasoning": "Rich cultural heritage, beautiful temples, gardens, and traditional experiences.",
                    "highlights": ["Fushimi Inari", "Bamboo Forest", "Temples", "Traditional Districts", "Cuisine"],
                    "estimated_daily_cost": 180,
                    "best_for": "Cultural immersion and history",
                    "considerations": "Language barrier possible"
                }
            ]
        
        return {
            "destinations": fallback_dest[:3],
            "reasoning_summary": f"Using fallback recommendations due to processing error. Based on {travel_style} style and {budget_cat} budget.",
            "fallback_mode": True,
            "error": error
        }
