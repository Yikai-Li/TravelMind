"""
TravelMind Flask API Server
REST API endpoints for travel planning
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from orchestrator import TravelMindOrchestrator
from utils import get_debug_trace
from api_streaming import create_streaming_enrichment_endpoint
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize orchestrator
orchestrator = TravelMindOrchestrator()

# Add streaming endpoint
create_streaming_enrichment_endpoint(app, orchestrator)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "TravelMind API",
        "version": "1.0.0"
    })


@app.route('/api/plan', methods=['POST'])
def generate_plan():
    """
    Generate a new travel plan
    
    Request Body:
    {
        "dates": "2024-06-15 to 2024-06-22",
        "departure_city": "New York",
        "budget": 3000,
        "travel_style": "adventure",
        "interests": ["hiking", "local culture"],
        "pace": "moderate",
        "group_type": "solo",
        "detail_level": "full",  // "high_level", "medium", or "full"
        "debug_mode": false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "error": "No data provided"
            }), 400
        
        # Extract detail level and debug mode
        detail_level = data.pop("detail_level", "full")
        debug_mode = data.pop("debug_mode", False)
        
        # Generate plan
        result = orchestrator.generate_plan(
            user_input=data,
            detail_level=detail_level,
            debug_mode=debug_mode
        )
        
        status_code = 200 if result.get("status") == "success" else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "An unexpected error occurred"
        }), 500


@app.route('/api/refine', methods=['POST'])
def refine_plan():
    """
    Refine an existing plan
    
    Request Body:
    {
        "plan_id": "abc123",
        "refinements": {
            "budget": 4000,
            "pace": "relaxed"
        },
        "debug_mode": false
    }
    """
    try:
        data = request.get_json()
        
        plan_id = data.get("plan_id")
        if not plan_id:
            return jsonify({
                "status": "error",
                "error": "plan_id is required"
            }), 400
        
        refinements = data.get("refinements", {})
        debug_mode = data.get("debug_mode", False)
        
        result = orchestrator.refine_plan(
            plan_id=plan_id,
            refinements=refinements,
            debug_mode=debug_mode
        )
        
        status_code = 200 if result.get("status") == "success" else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/alternatives', methods=['POST'])
def get_alternatives():
    """
    Get alternative destinations for a plan
    
    Request Body:
    {
        "plan_id": "abc123",
        "count": 3
    }
    """
    try:
        data = request.get_json()
        
        plan_id = data.get("plan_id")
        if not plan_id:
            return jsonify({
                "status": "error",
                "error": "plan_id is required"
            }), 400
        
        count = data.get("count", 3)
        
        result = orchestrator.get_alternatives(
            plan_id=plan_id,
            count=count
        )
        
        status_code = 200 if result.get("status") == "success" else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/plan/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """
    Retrieve a plan by ID
    """
    try:
        plan = orchestrator.get_plan(plan_id)
        
        if not plan:
            return jsonify({
                "status": "error",
                "error": "Plan not found"
            }), 404
        
        return jsonify(plan), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/debug/<plan_id>', methods=['GET'])
def get_debug(plan_id):
    """
    Get debug trace for a plan
    """
    try:
        trace = get_debug_trace(plan_id)
        
        if not trace:
            return jsonify({
                "status": "error",
                "error": "Debug trace not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "trace": trace
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/enrich-single-activity', methods=['POST'])
def enrich_single_activity():
    """
    Enrich a single activity with detailed information
    """
    try:
        data = request.get_json()
        activity = data.get('activity')
        destination = data.get('destination')
        day_number = data.get('day_number')
        
        if not activity:
            return jsonify({
                "status": "error",
                "error": "activity data required"
            }), 400
        
        # Use dual model enricher with error handling
        try:
            from agents.dual_model_enricher import DualModelEnricher
            enricher = DualModelEnricher()
            
            enriched = enricher.enrich_activity(activity, destination, day_number)
            
            return jsonify({
                "status": "success",
                "data": enriched
            }), 200
        except Exception as enrichment_error:
            print(f"Enrichment error: {enrichment_error}")
            # Return basic enriched data as fallback
            return jsonify({
                "status": "success",
                "data": {
                    **activity,
                    "description": f"Information about {activity.get('name')} in {destination}",
                    "tips": ["Check opening hours before visiting", "Consider booking in advance"],
                    "cost": activity.get('cost_estimate', 'Varies')
                }
            }), 200
        
    except Exception as e:
        print(f"API error in enrich-single-activity: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Failed to enrich activity"
        }), 500


@app.route('/api/regenerate-day', methods=['POST'])
def regenerate_day():
    """
    Regenerate a specific day of itinerary
    
    Request Body:
    {
        "plan_id": "abc123",
        "day_number": 3,
        "adjustments": {}
    }
    """
    try:
        data = request.get_json()
        
        plan_id = data.get("plan_id")
        day_number = data.get("day_number")
        
        if not plan_id or not day_number:
            return jsonify({
                "status": "error",
                "error": "plan_id and day_number are required"
            }), 400
        
        adjustments = data.get("adjustments")
        
        result = orchestrator.regenerate_day(
            plan_id=plan_id,
            day_number=day_number,
            adjustments=adjustments
        )
        
        status_code = 200 if result.get("status") == "success" else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          TravelMind API Server Starting                  ║
║                                                          ║
║  Server: http://localhost:{port}                          ║
║  Health: http://localhost:{port}/api/health               ║
║                                                          ║
║  Endpoints:                                              ║
║  POST /api/plan - Generate travel plan                   ║
║  POST /api/refine - Refine existing plan                 ║
║  POST /api/alternatives - Get alternative destinations   ║
║  GET  /api/plan/<id> - Retrieve plan                     ║
║  GET  /api/debug/<id> - Get debug trace                  ║
║                                                          ║
║  Note: Set OPENAI_API_KEY environment variable           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
