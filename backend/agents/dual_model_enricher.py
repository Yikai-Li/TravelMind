"""
Dual Model Detail Enrichment Agent
Uses travel-agent model + OpenAI + web scraping for comprehensive enrichment
"""
from typing import Dict, Any, List
from utils import call_llm, parse_json_response
import requests
from bs4 import BeautifulSoup
import re
import os
import torch


class DualModelEnricher:
    """
    Agent using both travel-agent model and OpenAI for enrichment
    """
    
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        self.travel_pipe = None
        
        # Try to load HuggingFace model if token available
        if self.hf_token:
            try:
                from transformers import pipeline
                from huggingface_hub import login
                
                login(self.hf_token)
                print("Loading HuggingFace travel-agent model...")
                
                self.travel_pipe = pipeline(
                    "text-generation",
                    model="Yanncccd/travel-agent-8b-v2",
                    model_kwargs={"torch_dtype": torch.float16},
                    device_map="auto"
                )
                print("✓ Travel agent model loaded successfully")
            except Exception as e:
                print(f"Could not load HF model: {e}")
                print("Falling back to OpenAI only")
    
    def enrich_activity(self, activity: Dict[str, Any], destination: str, day_number: int) -> Dict[str, Any]:
        """
        Enrich a single activity with detailed information and sources
        """
        try:
            activity_name = activity.get('name', '')
            activity_type = activity.get('type', '')
            
            print(f"Enriching: {activity_name} in {destination}")
        except Exception as e:
            print(f"Error in enrich_activity setup: {e}")
            return self._basic_enrichment(activity)
        
        # Build context-aware enrichment prompt
        if 'hotel' in activity_name.lower() or 'check-in' in activity_name.lower() or 'accommodation' in activity_name.lower():
            prompt = f"""Provide detailed hotel check-in information for {destination}:

Activity: {activity_name}
Location: {destination}
Day: {day_number}

Provide:
1. Recommended hotel areas in {destination}
2. Average hotel price range
3. Link to search hotels on Booking.com for {destination}
4. Airport/arrival transportation options to hotels
5. Check-in timing and tips
6. **3-4 specific hotel examples with different price ranges**

Format as JSON with:
{{
  "description": "...",
  "time_slot": "...",
  "cost_details": "...",
  "transport_notes": "...",
  "booking_url": "...",
  "sources": [],
  "hotel_examples": [
    {{
      "name": "Hotel Name",
      "category": "Budget/Mid-Range/Upscale/Luxury",
      "price_per_night": "$XX-$XX",
      "location": "Neighborhood/Area",
      "amenities": "key amenities"
    }}
  ]
}}
"""
        elif activity_type == 'dining' or 'lunch' in activity_name.lower() or 'dinner' in activity_name.lower() or 'breakfast' in activity_name.lower() or 'restaurant' in activity_name.lower() or 'dining' in activity_name.lower() or 'meal' in activity_name.lower():
            prompt = f"""Provide detailed dining information and specific restaurant recommendations for {destination}:

Activity: {activity_name}
Location: {destination}
Day: {day_number}

Provide:
1. Description of dining scene/area
2. Recommended dining time
3. Average cost per person
4. **3-4 specific restaurant recommendations** covering different cuisines and price ranges

Format as JSON with:
{{
  "description": "...",
  "time_slot": "...",
  "cost_details": "...",
  "transport_notes": "...",
  "tips": [],
  "restaurant_options": [
    {{
      "name": "Restaurant Name",
      "cuisine": "Type of cuisine",
      "price_range": "$/$$/$$$/$$$$",
      "specialties": "signature dishes"
    }}
  ],
  "sources": []
}}
"""
        elif activity_type == 'sightseeing' or activity_type == 'cultural':
            prompt = f"""Check if this attraction is currently available and provide details:

Activity: {activity_name}
Location: {destination}

IMPORTANT:
1. Check if this attraction has any closures, renovations, or alerts
2. Provide official website link
3. Include current ticket prices if available
4. Opening hours
5. How to get there from city center

Format as JSON:
{{
  "description": "...",
  "availability_status": "open" or "closed" or "limited",
  "closure_notice": "..." if closed/limited,
  "time_slot": "recommended visit time",
  "cost_details": "entrance fee details",
  "booking_url": "official website",
  "transport_notes": "how to get there",
  "tips": [],
  "sources": ["official website"]
}}"""
        else:
            prompt = f"""Provide detailed information for this travel activity:

Activity: {activity_name}
Type: {activity_type}
Location: {destination}

Provide: description, specific timing, costs, booking info, transport, tips, official links, sources

Format as JSON"""
        
        try:
            # Use OpenAI for enrichment
            response = call_llm(
                system_prompt="You are a travel expert providing detailed, accurate information with sources.",
                user_prompt=prompt,
                temperature=0.6
            )
            
            enriched = parse_json_response(response)
            
            # Try to scrape additional info if URL provided
            if enriched.get('booking_url') or enriched.get('sources'):
                url = enriched.get('booking_url') or (enriched.get('sources', [None])[0])
                if url:
                    scraped_info = self._scrape_additional_info(url, activity_name)
                    if scraped_info:
                        enriched['scraped_details'] = scraped_info
            
            # Merge with original activity
            result = activity.copy()
            result.update(enriched)
            
            return result
            
        except Exception as e:
            print(f"Error enriching {activity_name}: {e}")
            # Return activity with basic enrichment
            return self._basic_enrichment(activity)
    
    def _scrape_additional_info(self, url: str, activity_name: str) -> Dict[str, Any]:
        """
        Scrape additional information from official websites
        """
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract price information
            price_patterns = [r'\$\d+', r'€\d+', r'£\d+', r'\d+\s*USD']
            text = soup.get_text()
            prices = []
            for pattern in price_patterns:
                found = re.findall(pattern, text[:1000])  # Search first 1000 chars
                prices.extend(found)
            
            # Extract hours
            hours = re.findall(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)', text[:2000])
            
            return {
                'found_prices': prices[:3] if prices else [],
                'found_hours': hours[:3] if hours else [],
                'source_url': url
            }
            
        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            return None
    
    def enrich_transportation(self, origin: str, destination: str, destination_country: str, is_outbound: bool = True) -> Dict[str, Any]:
        """
        Enrich transportation information between two cities
        """
        direction = "to" if is_outbound else "from"
        print(f"Enriching transportation: {origin} {direction} {destination}")
        
        prompt = f"""Provide detailed transportation options from {origin} to {destination}, {destination_country}:

Direction: {"Outbound (going to destination)" if is_outbound else "Return (coming back home)"}

Provide comprehensive transportation details:
1. Flight options (airlines, approximate duration, price range)
2. Alternative transportation (train, bus, car) if applicable
3. Airport/station names and codes
4. Estimated travel time for each option
5. Average costs for each option
6. Booking recommendations and websites
7. Tips for this specific route

Format as JSON with:
{{
  "name": "Transportation: {origin} to {destination}",
  "type": "transportation",
  "description": "Detailed overview of transport options",
  "options": [
    {{
      "mode": "flight/train/bus/car",
      "details": "specific details",
      "duration": "estimated time",
      "cost_range": "price range",
      "providers": ["airline/company names"],
      "booking_url": "where to book"
    }}
  ],
  "recommended_option": "which option is best",
  "tips": ["practical travel tips"],
  "sources": ["booking website URLs"]
}}"""
        
        try:
            response = call_llm(
                system_prompt="You are a travel transportation expert providing accurate route and booking information.",
                user_prompt=prompt,
                temperature=0.5
            )
            
            enriched = parse_json_response(response)
            enriched['is_transportation'] = True
            enriched['is_outbound'] = is_outbound
            
            return enriched
            
        except Exception as e:
            print(f"Error enriching transportation: {e}")
            # Return basic transportation info
            return {
                "name": f"Transportation: {origin} to {destination}",
                "type": "transportation",
                "description": f"Travel from {origin} to {destination}. Check flight aggregators like Google Flights, Skyscanner, or Kayak for the best options.",
                "tips": [
                    "Book flights 2-3 months in advance for best prices",
                    "Compare prices across multiple booking sites",
                    "Consider airport location and transfer times"
                ],
                "is_transportation": True,
                "is_outbound": is_outbound
            }
    
    def _basic_enrichment(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide basic enrichment when full enrichment fails
        """
        result = activity.copy()
        
        # Add defaults
        if not result.get('description'):
            result['description'] = f"Enjoy {activity.get('name')} - a great {activity.get('type', 'travel')} experience."
        
        if not result.get('cost_estimate'):
            type_costs = {
                'dining': 30,
                'sightseeing': 20,
                'adventure': 60,
                'cultural': 15,
                'relaxation': 40
            }
            result['cost_estimate'] = type_costs.get(activity.get('type', ''), 25)
        
        if not result.get('tips'):
            result['tips'] = ["Check opening hours in advance", "Book tickets online if possible"]
        
        return result
