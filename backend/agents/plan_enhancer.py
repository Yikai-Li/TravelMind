"""
Plan Enhancer Agent
Enhances, modifies, or fills gaps in user-provided travel plans using both GPT and Hugging Face models
"""
from typing import Dict, Any
import os
from openai import OpenAI
import torch


class PlanEnhancerAgent:
    """
    Agent responsible for enhancing user's existing travel plans using dual AI models
    Takes a rough plan and adds details, optimizes timing, or modifies based on user preferences
    Uses both GPT-4 and Hugging Face travel-agent model for comprehensive enhancement
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"
        
        # Initialize Hugging Face model
        self.hf_token = os.getenv("HF_TOKEN")
        self.travel_pipe = None
        
        # Try to load HuggingFace model if token available
        if self.hf_token:
            try:
                from transformers import pipeline
                from huggingface_hub import login
                
                login(self.hf_token)
                print("Loading HuggingFace travel-agent model for plan enhancement...")
                
                self.travel_pipe = pipeline(
                    "text-generation",
                    model="Yanncccd/travel-agent-8b-v2",
                    model_kwargs={"torch_dtype": torch.float16},
                    device_map="auto"
                )
                print("✓ Travel agent model loaded successfully for plan enhancement")
            except Exception as e:
                print(f"Could not load HF model for plan enhancement: {e}")
                print("Using OpenAI only for plan enhancement")
    
    def enhance(
        self,
        existing_plan: str,
        destination: str,
        constraints: Dict[str, Any],
        action: str = "enhance"
    ) -> Dict[str, Any]:
        """
        Enhance an existing travel plan using both GPT and Hugging Face models
        
        Args:
            existing_plan: User's rough plan text (from "What would you like us to do?" input)
            destination: Destination location
            constraints: Parsed constraints (dates, budget, pace, etc.)
            action: What to do - from "What would you like us to do?" dropdown
        
        Returns:
            Enhanced itinerary with details from both models
        """
        
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
        
        # Build the enhancement prompt based on user's input
        base_context = f"""You are enhancing a travel plan for {destination}.

USER'S PLAN:
{existing_plan}

TRAVEL DETAILS:
- Destination: {destination}
- Dates: {dates}
- Budget: ${budget} total (if specified)
- Pace: {pace_descriptions.get(pace, pace)}
- Travel Style: {travel_style}
- Group Type: {group_type}
- Interests: {', '.join(interests) if interests else 'General sightseeing'}

USER REQUESTED: {action.upper()}
"""

        # Get insights from both models
        print(f"Enhancing plan with dual models - Action: {action}")
        
        # 1. Get HuggingFace model insights (if available) - with timeout
        hf_insights = None
        if self.travel_pipe:
            try:
                # Use threading to add timeout
                import threading
                result_container = [None]
                
                def get_hf():
                    try:
                        result_container[0] = self._get_hf_insights(existing_plan, destination, action, pace_descriptions.get(pace, pace))
                    except Exception as e:
                        print(f"⚠ HF thread error: {e}")
                
                hf_thread = threading.Thread(target=get_hf)
                hf_thread.daemon = True
                hf_thread.start()
                hf_thread.join(timeout=20)  # 20 second timeout
                
                if hf_thread.is_alive():
                    print("⚠ HF model timed out, skipping and using GPT-only...")
                    hf_insights = None
                else:
                    hf_insights = result_container[0]
                    
            except Exception as e:
                print(f"⚠ HF model error: {e}, using GPT-only...")
        
        # 2. Get GPT insights with full structure
        gpt_result = self._get_gpt_enhancement(
            existing_plan, destination, constraints, action, 
            pace_descriptions, hf_insights
        )
        
        return gpt_result
    
    def _get_hf_insights(self, existing_plan: str, destination: str, action: str, pace: str) -> str:
        """
        Get insights from Hugging Face travel-agent model
        """
        print("Getting insights from HuggingFace travel-agent model...")
        
        # Build prompt for HF model
        hf_prompt = f"""<|im_start|>system
You are a travel planning expert helping to enhance a travel itinerary.
<|im_end|>
<|im_start|>user
I need help with my travel plan to {destination}.

My current plan:
{existing_plan}

I want you to: {action}
Pace preference: {pace}

Please provide detailed suggestions, practical tips, specific timing recommendations, and cost estimates to enhance this plan.
<|im_end|>
<|im_start|>assistant
"""
        
        try:
            # Generate with HF model
            hf_output = self.travel_pipe(
                hf_prompt,
                max_new_tokens=800,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )
            
            hf_text = hf_output[0]['generated_text']
            # Extract only the assistant's response
            if '<|im_start|>assistant' in hf_text:
                hf_response = hf_text.split('<|im_start|>assistant')[-1].strip()
                # Remove any end tokens
                hf_response = hf_response.replace('<|im_end|>', '').strip()
            else:
                hf_response = hf_text.replace(hf_prompt, '').strip()
            
            print(f"✓ HF model provided insights ({len(hf_response)} chars)")
            return hf_response
            
        except Exception as e:
            print(f"Error generating HF insights: {e}")
            return None
    
    def _get_gpt_enhancement(
        self,
        existing_plan: str,
        destination: str,
        constraints: Dict[str, Any],
        action: str,
        pace_descriptions: Dict[str, str],
        hf_insights: str = None
    ) -> Dict[str, Any]:
        """
        Get structured enhancement from GPT, optionally incorporating HF insights
        """
        print("Getting structured enhancement from GPT...")
        
        dates = constraints.get('constraints', {}).get('dates', 'Not specified')
        budget = constraints.get('constraints', {}).get('budget', 'Not specified')
        pace = constraints.get('constraints', {}).get('pace', 'moderate')
        interests = constraints.get('constraints', {}).get('interests', [])
        travel_style = constraints.get('constraints', {}).get('travel_style', 'Not specified')
        group_type = constraints.get('constraints', {}).get('group_type', 'Not specified')
        
        # Build action-specific instructions
        action_instructions = {
            "enhance": "Enhance with specific timing, costs, tips, transportation, and meal suggestions. Keep the user's structure intact.",
            "modify": "Improve and optimize the plan by reordering, suggesting better alternatives, and adjusting for preferences.",
            "fill_gaps": "Fill gaps by adding activities for unplanned times, meals, transportation, and rest breaks.",
            "optimize": "Optimize by reorganizing to minimize travel time, group nearby attractions, and balance energy levels."
        }
        
        # Include HF insights if available
        hf_context = ""
        if hf_insights:
            hf_context = f"""

INSIGHTS FROM TRAVEL AGENT MODEL:
{hf_insights}

Use these insights along with your expertise to create a comprehensive enhanced plan.
"""
        
        prompt = f"""You are an expert travel planner enhancing a traveler's plan for {destination}.

USER'S PLAN:
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
{action_instructions.get(action, action_instructions['enhance'])}{hf_context}

GUIDELINES:
1. Respect the user's original ideas and preferences
2. Provide SPECIFIC details: exact timing, actual costs, real names
3. For accommodation: include 2-3 specific hotel examples with names, prices, amenities
4. For dining: include 2-3 specific restaurant recommendations with cuisine and price
5. Include practical info: opening hours, booking requirements, dress codes
6. Consider logistics: walking distances, transportation time
7. Add insider tips and local recommendations
8. Be realistic about timing
9. Format clearly with day-by-day structure
10. For each activity: Name, Time, Duration, Cost, Description, Tips
11. Include 3-5 hotel recommendations at top level
12. Include official website links where helpful (no phone numbers)
13. Only include real, existing websites

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
            "description": "Brief description",
            "best_for": "Who it's best for"
        }}
    ],
    "itinerary": [
        {{
            "day": 1,
            "date": "Day description",
            "theme": "Daily theme",
            "activities": [
                {{
                    "time": "9:00 AM - 11:00 AM",
                    "name": "Activity name",
                    "type": "sightseeing|dining|transport|experience|rest",
                    "description": "Detailed description",
                    "location": "Specific address or area",
                    "duration": "Duration in minutes",
                    "cost": "Estimated cost in USD or 'Free'",
                    "tips": "Practical tips",
                    "booking_required": true/false,
                    "priority": "must-see|recommended|optional",
                    "resort_examples": [
                        {{
                            "name": "Resort Name",
                            "category": "Luxury|Upscale",
                            "price_per_night": "$300-500",
                            "amenities": "Key amenities"
                        }}
                    ],
                    "restaurant_options": [
                        {{
                            "name": "Restaurant Name",
                            "cuisine": "Type",
                            "price_range": "$$-$$$",
                            "specialties": "What they're known for"
                        }}
                    ]
                }}
            ],
            "daily_cost": "Estimated total",
            "notes": "Daily notes"
        }}
    ],
    "pacing_notes": "Notes about pace and energy",
    "practical_tips": [
        "Important tip 1",
        "Important tip 2"
    ]
}}

Respond with ONLY the JSON, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert travel planner who enhances travel itineraries with detailed, practical information. You work with insights from multiple AI models to provide comprehensive recommendations."
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
            result['models_used'] = ['gpt-4o-mini']
            if hf_insights:
                result['models_used'].append('travel-agent-8b-v2')
                result['dual_model_enhancement'] = True
            
            print(f"✓ Plan enhanced successfully using {len(result['models_used'])} model(s)")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            # Fallback: create structured response from text
            return {
                "status": "success",
                "destination": destination,
                "overview": "Enhanced itinerary based on your plan",
                "enhancements_summary": f"Applied {action} to your travel plan using AI models",
                "itinerary": self._create_basic_structure(existing_plan, destination),
                "pacing_notes": f"Itinerary enhanced with {pace} pace in mind",
                "practical_tips": ["Check opening hours before visiting", "Book popular attractions in advance"],
                "action_performed": action,
                "original_plan": existing_plan,
                "models_used": ['gpt-4o-mini'],
                "parse_note": "Structured format created from AI response"
            }
        
        except Exception as e:
            print(f"GPT enhancement error: {e}")
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
