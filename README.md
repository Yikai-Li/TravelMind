# TravelMind - AI-Powered Travel Planning Demo

TravelMind is an LLM-powered travel planning application that generates personalized itineraries through progressive, interactive refinement.

## Features

- **Flexible User Input**: Accepts minimal to rich inputs (dates, departure city, budget, travel style, interests, pace, group type, constraints)
- **Adaptive Planning Output**: Generates high-level recommendations to fully detailed day-by-day itineraries
- **LLM Agent-Based Pipeline**: 
  - Constraint Parsing Agent
  - Destination Recommendation Agent
  - Itinerary Planning Agent
  - Detail Enrichment Agent
- **Interactive Refinement**: Regenerate plans, adjust constraints, request alternatives
- **Transparency**: Includes reasoning, assumptions, warnings, and optional debug mode
- **Robust Error Handling**: Graceful degradation and fallback strategies

## Project Structure

```
travelmind/
├── backend/               # Python Flask backend
│   ├── agents/           # LLM agent implementations
│   ├── orchestrator.py   # Central orchestrator
│   ├── api.py            # REST API endpoints
│   └── utils.py          # Helper functions
├── frontend/             # React/Next.js frontend
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Next.js pages
│   │   └── utils/        # Frontend utilities
└── requirements.txt      # Python dependencies
```

## Setup Instructions

### Backend

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file
OPENAI_API_KEY=your_api_key_here
```

3. Run the backend server:
```bash
python api.py
```

### Frontend

1. Install Node dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open http://localhost:3000 in your browser

## API Endpoints

- `POST /api/plan` - Generate initial travel plan
- `POST /api/refine` - Refine existing plan
- `POST /api/alternatives` - Get alternative destinations
- `GET /api/debug/:plan_id` - Get debug trace

## Usage Example

```json
{
  "dates": "2024-06-15 to 2024-06-22",
  "departure_city": "New York",
  "budget": 3000,
  "travel_style": "adventure",
  "interests": ["hiking", "local culture"],
  "pace": "moderate",
  "group_type": "solo"
}
```

## License

MIT
