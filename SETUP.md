# TravelMind Setup Guide

Complete setup instructions for the TravelMind AI-powered travel planning application.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- OpenAI API key

## Quick Start

### 1. Set Up Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cd backend
copy .env.example .env  # Windows
# or
cp .env.example .env    # Linux/Mac
```

Edit the `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Start the Backend Server

```bash
cd backend
python api.py
```

The backend server will start on http://localhost:5000

### 5. Start the Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will start on http://localhost:3000

### 6. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

## Running the Demo

To test the backend without the UI:

```bash
# From the project root
python demo.py
```

The demo script will:
1. Show high-level destination recommendations
2. Generate a full detailed itinerary
3. Demonstrate minimal input with assumptions

## Project Structure

```
AML Final Project/
├── backend/                 # Python Flask backend
│   ├── agents/             # LLM agent implementations
│   │   ├── __init__.py
│   │   ├── constraint_parser.py
│   │   ├── destination_recommender.py
│   │   ├── itinerary_planner.py
│   │   └── detail_enricher.py
│   ├── api.py              # Flask API server
│   ├── orchestrator.py     # Central orchestrator
│   ├── utils.py            # Utility functions
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Environment variables
├── frontend/               # React/Next.js frontend
│   ├── components/         # React components
│   │   ├── PlanningForm.js
│   │   ├── ItineraryView.js
│   │   └── DestinationsList.js
│   ├── pages/              # Next.js pages
│   │   ├── index.js
│   │   └── _app.js
│   ├── styles/             # CSS modules
│   ├── package.json
│   └── next.config.js
├── demo.py                 # Demo script
└── README.md              # Documentation
```

## API Endpoints

### POST /api/plan
Generate a new travel plan

**Request Body:**
```json
{
  "dates": "2024-06-15 to 2024-06-22",
  "departure_city": "New York",
  "budget": 3000,
  "travel_style": "adventure",
  "interests": ["hiking", "local culture"],
  "pace": "moderate",
  "group_type": "solo",
  "detail_level": "full"
}
```

### POST /api/refine
Refine an existing plan

**Request Body:**
```json
{
  "plan_id": "abc123",
  "refinements": {
    "budget": 4000,
    "pace": "relaxed"
  }
}
```

### POST /api/alternatives
Get alternative destinations

**Request Body:**
```json
{
  "plan_id": "abc123",
  "count": 3
}
```

### GET /api/plan/:plan_id
Retrieve a specific plan

### GET /api/debug/:plan_id
Get debug trace for a plan

## Configuration

### Backend Configuration

Edit `backend/.env`:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PORT`: Backend server port (default: 5000)
- `FLASK_ENV`: Environment mode (development/production)

### Frontend Configuration

The frontend reads the API URL from environment variables:
- Default: `http://localhost:5000`
- Can be changed in `frontend/next.config.js`

## Features

### 1. Flexible User Input
- Accept minimal to rich inputs
- Progressive disclosure approach
- Smart defaults and assumptions

### 2. Adaptive Planning Output
- **High Level**: Destination recommendations only
- **Medium**: Day-by-day outlines
- **Full**: Detailed itineraries with timing, costs, tips

### 3. LLM Agent Pipeline
- **Constraint Parser**: Normalizes user input
- **Destination Recommender**: Suggests destinations
- **Itinerary Planner**: Creates day-by-day plans
- **Detail Enricher**: Adds timing, costs, tips

### 4. Interactive Refinement
- Adjust budget, pace, or other constraints
- Request alternative destinations
- Regenerate specific days

### 5. Transparency
- Shows reasoning for recommendations
- Displays assumptions made
- Warns about potential issues
- Optional debug mode for agent traces

## Troubleshooting

### Backend Issues

**"Module not found" errors:**
```bash
pip install -r backend/requirements.txt
```

**"OPENAI_API_KEY not found":**
- Ensure `.env` file exists in backend directory
- Verify API key is correct
- On Windows: `set OPENAI_API_KEY=your_key`
- On Linux/Mac: `export OPENAI_API_KEY=your_key`

**Port already in use:**
- Change PORT in backend/.env
- Kill process using port 5000

### Frontend Issues

**"Cannot find module" errors:**
```bash
cd frontend
npm install
```

**Cannot connect to backend:**
- Ensure backend is running on port 5000
- Check API_BASE_URL in next.config.js
- Verify no CORS issues (CORS is enabled by default)

### Common Issues

**LLM responses are slow:**
- Normal for detailed plans (can take 30-60 seconds)
- Consider using "high_level" or "medium" detail levels for faster results

**JSON parsing errors:**
- Usually self-correcting due to retry logic
- Check if OpenAI API is accessible
- Verify API key has sufficient credits

## Development

### Running in Development Mode

Backend with auto-reload:
```bash
cd backend
set FLASK_ENV=development  # Windows
export FLASK_ENV=development  # Linux/Mac
python api.py
```

Frontend with hot reload:
```bash
cd frontend
npm run dev
```

### Building for Production

Frontend:
```bash
cd frontend
npm run build
npm start
```

## Support

For issues or questions:
1. Check this setup guide
2. Review the main README.md
3. Check the demo.py for usage examples
4. Review agent code for implementation details

## License

MIT License - See README.md for details
