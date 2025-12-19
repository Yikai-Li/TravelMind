"""
Streaming API endpoint for progressive enrichment
"""
from flask import Response, stream_with_context, request, jsonify
import json
from agents.dual_model_enricher import DualModelEnricher


def create_streaming_enrichment_endpoint(app, orchestrator):
    """
    Add streaming enrichment endpoint to Flask app
    """
    
    @app.route('/api/enrich-progressive', methods=['GET'])
    def enrich_progressive():
        """
        Progressively enrich an itinerary, streaming results as each activity is processed
        """
        def generate():
            try:
                plan_id = request.args.get('plan_id')
                
                plan = orchestrator.get_plan(plan_id)
                if not plan:
                    yield f"data: {json.dumps({'error': 'Plan not found'})}\n\n"
                    return
                
                enricher = DualModelEnricher()
                itinerary = plan.get('itinerary', [])
                destination_name = plan.get('destination', {}).get('name', 'destination')
                destination_country = plan.get('destination', {}).get('country', '')
                departure_city = plan.get('parsed_constraints', {}).get('constraints', {}).get('departure_city', '')
                
                # Send initial message
                total_activities = sum(len(day.get('activities', [])) for day in itinerary)
                if departure_city:
                    total_activities += 2  # Add transport to/from destination
                yield f"data: {json.dumps({'status': 'starting', 'total_activities': total_activities})}\n\n"
                
                # Initialize counter
                activity_count = 0
                
                # Add transportation from departure city to destination (Day 1)
                if departure_city and len(itinerary) > 0:
                    activity_count += 1
                    transport_to = enricher.enrich_transportation(
                        departure_city,
                        destination_name,
                        destination_country,
                        is_outbound=True
                    )
                    yield f"data: {json.dumps({'status': 'activity_enriched', 'day': -1, 'activity': -1, 'data': transport_to, 'count': activity_count, 'type': 'transport_to'})}\n\n"
                
                # Process each day and activity
                enriched_itinerary = []
                
                for day_idx, day in enumerate(itinerary):
                    enriched_day = day.copy()
                    enriched_activities = []
                    
                    for act_idx, activity in enumerate(day.get('activities', [])):
                        activity_count += 1
                        
                        # Enrich this activity
                        enriched_act = enricher.enrich_activity(
                            activity,
                            destination_name,
                            day.get('day_number', day_idx + 1)
                        )
                        
                        enriched_activities.append(enriched_act)
                        
                        # Stream this enriched activity
                        yield f"data: {json.dumps({'status': 'activity_enriched', 'day': day_idx, 'activity': act_idx, 'data': enriched_act, 'count': activity_count})}\n\n"
                    
                    enriched_day['activities'] = enriched_activities
                    enriched_itinerary.append(enriched_day)
                    
                    # Stream day completion
                    yield f"data: {json.dumps({'status': 'day_complete', 'day': day_idx})}\n\n"
                
                # Add return transportation from destination back to departure city (Last day)
                if departure_city and len(itinerary) > 0:
                    activity_count += 1
                    transport_back = enricher.enrich_transportation(
                        destination_name,
                        departure_city,
                        destination_country,
                        is_outbound=False
                    )
                    yield f"data: {json.dumps({'status': 'activity_enriched', 'day': len(itinerary), 'activity': -1, 'data': transport_back, 'count': activity_count, 'type': 'transport_back'})}\n\n"
                
                # Send completion
                yield f"data: {json.dumps({'status': 'complete', 'itinerary': enriched_itinerary})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    
    return app
