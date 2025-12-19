"""
TravelMind Orchestrator
Central orchestrator managing agent execution, regeneration, and partial updates
"""
from typing import Dict, Any, List, Optional
from agents import (
    ConstraintParserAgent,
    DestinationRecommenderAgent,
    ItineraryPlannerAgent,
    DetailEnricherAgent,
    PlanEnhancerAgent
)
from utils import generate_plan_id, store_debug_trace
from url_validator import filter_valid_sources
import time


class TravelMindOrchestrator:
    """
    Central orchestrator for managing the travel planning pipeline
    """
    
    def __init__(self):
        self.constraint_parser = ConstraintParserAgent()
        self.destination_recommender = DestinationRecommenderAgent()
        self.itinerary_planner = ItineraryPlannerAgent()
        self.detail_enricher = DetailEnricherAgent()
        self.plan_enhancer = PlanEnhancerAgent()
        
        # Storage for plans (in production, use a database)
        self.plans = {}
    
    def generate_plan(
        self,
        user_input: Dict[str, Any],
        detail_level: str = "full",
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a complete travel plan
        
        Args:
            user_input: User constraints and preferences
            detail_level: "high_level", "medium", or "full"
            debug_mode: Whether to include debug traces
        
        Returns:
            Complete travel plan with metadata
        """
        plan_id = generate_plan_id()
        start_time = time.time()
        
        trace = {
            "plan_id": plan_id,
            "user_input": user_input,
            "detail_level": detail_level,
            "steps": []
        }
        
        try:
            # Check if this is a plan enhancement request (user has existing plan)
            if user_input.get('existing_plan') and user_input.get('specific_destination'):
                return self.enhance_existing_plan(
                    user_input=user_input,
                    plan_id=plan_id,
                    debug_mode=debug_mode
                )
            
            # Step 1: Parse and normalize constraints
            step1_start = time.time()
            parsed_constraints = self.constraint_parser.parse(user_input)
            trace["steps"].append({
                "step": "constraint_parsing",
                "duration": time.time() - step1_start,
                "output": parsed_constraints
            })
            
            # Check for critical conflicts
            if parsed_constraints.get("conflicts"):
                return {
                    "plan_id": plan_id,
                    "status": "error",
                    "error": "Critical conflicts in constraints",
                    "conflicts": parsed_constraints["conflicts"],
                    "suggestions": "Please adjust your constraints and try again"
                }
            
            # Step 2: Recommend destinations OR use specific destination if provided
            step2_start = time.time()
            
            # Check if user specified a specific destination
            if user_input.get('specific_destination'):
                # Create a single destination entry based on user's selection
                recommendations = {
                    "destinations": [{
                        "name": user_input['specific_destination'].split(',')[0].strip(),
                        "country": user_input['specific_destination'].split(',')[1].strip() if ',' in user_input['specific_destination'] else "Unknown",
                        "score": 100,
                        "reasoning": f"Selected by user: {user_input['specific_destination']}",
                        "highlights": [],
                        "estimated_daily_cost": parsed_constraints.get('daily_budget', 100),
                        "best_for": "User's choice",
                        "considerations": ""
                    }],
                    "reasoning_summary": "Using user-selected destination"
                }
            else:
                # Normal recommendation flow
                destination_count = 5 if detail_level == "high_level" else 1
                recommendations = self.destination_recommender.recommend(
                    parsed_constraints,
                    count=destination_count
                )
            trace["steps"].append({
                "step": "destination_recommendation",
                "duration": time.time() - step2_start,
                "output": recommendations
            })
            
            # For high-level, return only recommendations
            if detail_level == "high_level":
                result = {
                    "plan_id": plan_id,
                    "status": "success",
                    "level": "high_level",
                    "destinations": recommendations["destinations"],
                    "reasoning": recommendations.get("reasoning_summary", ""),
                    "parsed_constraints": parsed_constraints,
                    "warnings": parsed_constraints.get("warnings", []),
                    "assumptions": parsed_constraints.get("assumptions", []),
                    "processing_time": time.time() - start_time
                }
                
                self.plans[plan_id] = result
                if debug_mode:
                    store_debug_trace(plan_id, trace)
                    result["debug_trace"] = trace
                
                return result
            
            # Step 3: Generate itinerary for top destination
            top_destination = recommendations["destinations"][0]
            step3_start = time.time()
            itinerary = self.itinerary_planner.plan(
                top_destination,
                parsed_constraints
            )
            trace["steps"].append({
                "step": "itinerary_planning",
                "duration": time.time() - step3_start,
                "output": itinerary
            })
            
            # For medium detail, return itinerary without enrichment
            if detail_level == "medium":
                result = {
                    "plan_id": plan_id,
                    "status": "success",
                    "level": "medium",
                    "destination": top_destination,
                    "itinerary": itinerary["itinerary"],
                    "overview": itinerary.get("overview", ""),
                    "pacing_notes": itinerary.get("pacing_notes", ""),
                    "alternative_destinations": recommendations["destinations"][1:] if len(recommendations["destinations"]) > 1 else [],
                    "parsed_constraints": parsed_constraints,
                    "warnings": parsed_constraints.get("warnings", []),
                    "assumptions": parsed_constraints.get("assumptions", []),
                    "processing_time": time.time() - start_time
                }
                
                self.plans[plan_id] = result
                if debug_mode:
                    store_debug_trace(plan_id, trace)
                    result["debug_trace"] = trace
                
                return result
            
            # Step 4: Enrich with details (full level)
            step4_start = time.time()
            enriched = self.detail_enricher.enrich(
                itinerary,
                top_destination,
                parsed_constraints
            )
            trace["steps"].append({
                "step": "detail_enrichment",
                "duration": time.time() - step4_start,
                "output": {"enrichment_level": enriched.get("enrichment_level")}
            })
            
            # Build full result
            result = {
                "plan_id": plan_id,
                "status": "success",
                "level": "full",
                "destination": top_destination,
                "itinerary": enriched["itinerary"],
                "overview": enriched.get("overview", ""),
                "pacing_notes": enriched.get("pacing_notes", ""),
                "enrichment_level": enriched.get("enrichment_level", "detailed"),
                "alternative_destinations": recommendations["destinations"][1:] if len(recommendations["destinations"]) > 1 else [],
                "parsed_constraints": parsed_constraints,
                "warnings": parsed_constraints.get("warnings", []),
                "assumptions": parsed_constraints.get("assumptions", []),
                "processing_time": time.time() - start_time
            }
            
            self.plans[plan_id] = result
            if debug_mode:
                store_debug_trace(plan_id, trace)
                result["debug_trace"] = trace
            
            return result
            
        except Exception as e:
            trace["error"] = str(e)
            if debug_mode:
                store_debug_trace(plan_id, trace)
            
            return {
                "plan_id": plan_id,
                "status": "error",
                "error": str(e),
                "message": "An error occurred during plan generation",
                "debug_trace": trace if debug_mode else None
            }
    
    def refine_plan(
        self,
        plan_id: str,
        refinements: Dict[str, Any],
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Refine an existing plan based on user feedback
        
        Args:
            plan_id: ID of existing plan
            refinements: Changes to apply (e.g., new budget, pace)
            debug_mode: Whether to include debug traces
        
        Returns:
            Refined travel plan
        """
        if plan_id not in self.plans:
            return {
                "status": "error",
                "error": "Plan not found",
                "plan_id": plan_id
            }
        
        original_plan = self.plans[plan_id]
        
        # Merge refinements with original constraints
        original_constraints = original_plan.get("parsed_constraints", {})
        merged_input = original_constraints.get("constraints", {}).copy()
        merged_input.update(refinements)
        
        # Regenerate with merged constraints
        return self.generate_plan(
            merged_input,
            detail_level=original_plan.get("level", "full"),
            debug_mode=debug_mode
        )
    
    def get_alternatives(
        self,
        plan_id: str,
        count: int = 3
    ) -> Dict[str, Any]:
        """
        Get alternative destinations for an existing plan
        
        Args:
            plan_id: ID of existing plan
            count: Number of alternatives to generate
        
        Returns:
            Alternative destination recommendations
        """
        if plan_id not in self.plans:
            return {
                "status": "error",
                "error": "Plan not found"
            }
        
        original_plan = self.plans[plan_id]
        parsed_constraints = original_plan.get("parsed_constraints", {})
        
        # Get new recommendations
        recommendations = self.destination_recommender.recommend(
            parsed_constraints,
            count=count + 1  # Get extra to exclude current destination
        )
        
        current_dest = original_plan.get("destination", {}).get("name", "")
        
        # Filter out current destination
        alternatives = [
            d for d in recommendations["destinations"]
            if d.get("name") != current_dest
        ][:count]
        
        return {
            "status": "success",
            "plan_id": plan_id,
            "alternatives": alternatives,
            "current_destination": current_dest
        }
    
    def regenerate_day(
        self,
        plan_id: str,
        day_number: int,
        adjustments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Regenerate a specific day of itinerary
        
        Args:
            plan_id: ID of existing plan
            day_number: Day to regenerate (1-indexed)
            adjustments: Optional adjustments for this day
        
        Returns:
            Updated plan with regenerated day
        """
        if plan_id not in self.plans:
            return {
                "status": "error",
                "error": "Plan not found"
            }
        
        # In a full implementation, this would regenerate just one day
        # For now, return the original plan with a note
        return {
            "status": "success",
            "message": "Day regeneration feature - would regenerate specific day",
            "plan_id": plan_id,
            "day_number": day_number
        }
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a plan by ID"""
        return self.plans.get(plan_id)
    
    def enhance_existing_plan(
        self,
        user_input: Dict[str, Any],
        plan_id: str,
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Enhance a user's existing travel plan
        
        Args:
            user_input: User input including existing_plan, specific_destination, plan_action
            plan_id: Generated plan ID for this enhancement
            debug_mode: Whether to include debug traces
        
        Returns:
            Enhanced travel plan with details
        """
        start_time = time.time()
        
        trace = {
            "plan_id": plan_id,
            "user_input": user_input,
            "mode": "plan_enhancement",
            "steps": []
        }
        
        try:
            # Step 1: Parse constraints (for additional context like pace, dates)
            step1_start = time.time()
            parsed_constraints = self.constraint_parser.parse(user_input)
            trace["steps"].append({
                "step": "constraint_parsing",
                "duration": time.time() - step1_start,
                "output": parsed_constraints
            })
            
            # Extract key fields
            existing_plan = user_input.get('existing_plan', '')
            destination = user_input.get('specific_destination', 'Unknown destination')
            plan_action = user_input.get('plan_action', 'enhance')
            
            if not existing_plan:
                return {
                    "plan_id": plan_id,
                    "status": "error",
                    "error": "No existing plan provided",
                    "message": "Please provide your existing travel plan to enhance"
                }
            
            # Step 2: Enhance the plan using the PlanEnhancerAgent
            step2_start = time.time()
            enhanced_result = self.plan_enhancer.enhance(
                existing_plan=existing_plan,
                destination=destination,
                constraints=parsed_constraints,
                action=plan_action
            )
            trace["steps"].append({
                "step": "plan_enhancement",
                "duration": time.time() - step2_start,
                "action": plan_action,
                "output": {"status": enhanced_result.get("status")}
            })
            
            if enhanced_result.get("status") == "error":
                return {
                    "plan_id": plan_id,
                    "status": "error",
                    "error": enhanced_result.get("error", "Enhancement failed"),
                    "message": enhanced_result.get("message", "Failed to enhance plan")
                }
            
            # Create destination object
            dest_parts = destination.split(',')
            destination_obj = {
                "name": dest_parts[0].strip() if len(dest_parts) > 0 else destination,
                "country": dest_parts[1].strip() if len(dest_parts) > 1 else "Unknown",
                "score": 100,
                "reasoning": f"User's chosen destination: {destination}",
                "highlights": [],
                "best_for": "User's plan"
            }
            
            # Build result in similar format to standard itinerary
            result = {
                "plan_id": plan_id,
                "status": "success",
                "level": "enhanced",
                "mode": "plan_enhancement",
                "destination": destination_obj,
                "itinerary": enhanced_result.get("itinerary", []),
                "overview": enhanced_result.get("overview", ""),
                "enhancements_summary": enhanced_result.get("enhancements_summary", ""),
                "pacing_notes": enhanced_result.get("pacing_notes", ""),
                "practical_tips": enhanced_result.get("practical_tips", []),
                "total_estimated_cost": enhanced_result.get("total_estimated_cost"),
                "hotel_recommendations": enhanced_result.get("hotel_recommendations", []),
                "action_performed": enhanced_result.get("action_performed", plan_action),
                "original_plan": existing_plan,
                "parsed_constraints": parsed_constraints,
                "warnings": parsed_constraints.get("warnings", []),
                "assumptions": parsed_constraints.get("assumptions", []),
                "processing_time": time.time() - start_time
            }
            
            # Validate and filter URLs in the result
            try:
                result = filter_valid_sources(result)
                print(f"✓ URL validation completed for plan {plan_id}")
            except Exception as url_error:
                print(f"URL validation error: {url_error}")
                # Continue without validation if it fails
            
            self.plans[plan_id] = result
            if debug_mode:
                store_debug_trace(plan_id, trace)
                result["debug_trace"] = trace
            
            return result
            
        except Exception as e:
            trace["error"] = str(e)
            if debug_mode:
                store_debug_trace(plan_id, trace)
            
            return {
                "plan_id": plan_id,
                "status": "error",
                "error": str(e),
                "message": "An error occurred during plan enhancement",
                "debug_trace": trace if debug_mode else None
            }
