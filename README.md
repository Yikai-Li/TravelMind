# TravelMind - AI-Powered Travel Planning System

TravelMind is an LLM-powered travel planning application that generates personalized itineraries through progressive, interactive refinement using a multi-agent architecture with dual AI models.

## 🎯 Features

- **Two Planning Modes**:
  - **Discover Destinations**: AI recommends destinations based on your preferences
  - **I Have a Plan**: Enhance your existing travel plans with AI-powered suggestions

- **Flexible User Input**: Accepts minimal to rich inputs (dates, departure city, budget, travel style, interests, pace, group type)
- **Adaptive Planning Output**: Generates high-level recommendations to fully detailed day-by-day itineraries
- **Dual-Model Enhancement**: Uses both GPT-4 and HuggingFace travel-agent model for comprehensive plan refinement
- **LLM Agent-Based Pipeline**: Multi-agent architecture with specialized agents for different planning aspects
- **Interactive Refinement**: Regenerate plans, adjust constraints, request alternatives
- **Progressive Enrichment**: Streaming enrichment of activities with real-time updates
- **Transparency**: Includes reasoning, assumptions, warnings, and optional debug mode
- **Robust Error Handling**: Graceful degradation and fallback strategies with timeout protection
- **URL Validation**: Automatic validation of external sources and recommendations

## 📁 Complete Project Structure

```
AML Final Project/
├── README.md                              # Main project documentation
├── SETUP.md                               # Detailed setup instructions
├── PLAN_ENHANCEMENT_CHANGES.md            # Dual-model enhancement documentation
├── test_backend.py                        # Backend testing script
├── architecture_diagram.html              # Visual architecture diagram
│
├── backend/                               # Python Flask backend
│   ├── __init__.py                        # Backend package initializer
│   ├── .env                              # Environment variables (API keys)
│   ├── .env.example                      # Environment template
│   ├── requirements.txt                  # Python dependencies
│   │
│   ├── api.py                            # Main REST API endpoints
│   ├── api_streaming.py                  # Streaming endpoints for progressive enrichment
│   ├── orchestrator.py                   # Central orchestrator managing agent pipeline
│   ├── utils.py                          # Utility functions (LLM calls, JSON parsing, etc.)
│   ├── url_validator.py                  # URL validation and filtering utilities
│   ├── demo.py                           # Demo scripts for testing
│   │
│   └── agents/                           # LLM Agent implementations
│       ├── __init__.py                   # Agents package initializer
│       ├── constraint_parser.py          # Parse and validate user constraints
│       ├── destination_recommender.py    # Recommend destinations based on preferences
│       ├── itinerary_planner.py          # Generate day-by-day itineraries
│       ├── detail_enricher.py            # Add detailed information to activities
│       ├── dual_model_enricher.py        # Enhanced enrichment with multiple models
│       └── plan_enhancer.py              # Enhance existing user plans (DUAL-MODEL)
│
└── frontend/                             # Next.js React frontend
    ├── package.json                      # Node.js dependencies
    ├── package-lock.json                 # Lock file for dependencies
    ├── next.config.js                    # Next.js configuration
    │
    ├── pages/                            # Next.js pages (routing)
    │   ├── _app.js                       # Custom App component
    │   └── index.js                      # Main page / entry point
    │
    ├── components/                       # React components
    │   ├── PlanningForm.js               # User input form (2 modes: Discover/Plan)
    │   ├── DestinationsList.js           # Display destination recommendations
    │   ├── ItineraryView.js              # Display detailed itinerary
    │   └── LoadingScreen.js              # Loading states with animations
    │
    └── styles/                           # CSS modules for styling
        ├── globals.css                   # Global styles
        ├── Home.module.css               # Home page styles
        ├── PlanningForm.module.css       # Form component styles
        ├── DestinationsList.module.css   # Destinations list styles
        ├── ItineraryView.module.css      # Itinerary view styles
        └── LoadingScreen.module.css      # Loading screen styles
```

## 🏗️ Architecture Overview

### System Architecture

TravelMind uses a **multi-agent orchestration pattern** with dual AI models for enhanced planning capabilities:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React/Next.js)                     │
│  ┌──────────────────┐                   ┌──────────────────┐        │
│  │ Discover Mode    │                   │ Plan Mode        │        │
│  │ (Find Dest.)     │                   │ (Enhance Plan)   │        │
│  └────────┬─────────┘                   └────────┬─────────┘        │
└───────────┼──────────────────────────────────────┼──────────────────┘
            │                                       │
            ├───────────────┐   ┌──────────────────┤
            ↓               ↓   ↓                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       Backend API (Flask)                            │
│  ┌──────────────┐                         ┌──────────────┐          │
│  │ /api/plan    │                         │ /api/plan    │          │
│  │ (discover)   │                         │ (enhance)    │          │
│  └──────┬───────┘                         └──────┬───────┘          │
└─────────┼────────────────────────────────────────┼──────────────────┘
          │                                         │
          ↓                                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        Orchestrator                                  │
│  ┌──────────────────┐                   ┌──────────────────┐        │
│  │ generate_plan()  │                   │ enhance_existing │        │
│  │                  │                   │ _plan()          │        │
│  └────────┬─────────┘                   └────────┬─────────┘        │
└───────────┼──────────────────────────────────────┼──────────────────┘
            │                                       │
            ↓                                       ↓
┌─────────────────────────────┐    ┌──────────────────────────────────┐
│   Discover Flow Agents      │    │   Enhancement Flow               │
│                              │    │                                  │
│  1. ConstraintParser         │    │  1. ConstraintParser             │
│  2. DestinationRecommender   │    │  2. PlanEnhancer (DUAL-MODEL)    │
│  3. ItineraryPlanner         │    │     ├─→ HuggingFace Model        │
│  4. DetailEnricher           │    │     │   (travel-agent-8b-v2)     │
│     └─→ DualModelEnricher    │    │     │   [20s timeout]            │
│                              │    │     └─→ GPT-4 Model              │
│                              │    │         (structured output)      │
└──────────────────────────────┘    └──────────────────────────────────┘
            │                                       │
            ↓                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      External Services                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │ OpenAI API   │   │ HuggingFace  │   │ Web Scraping │            │
│  │ (GPT-4)      │   │ Hub          │   │ (Optional)   │            │
│  └──────────────┘   └──────────────┘   └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Diagrams

### Discover Destinations Flow

```
User Input (Discover Mode)
    ↓
Frontend Form
    ↓
POST /api/plan
    ↓
Orchestrator.generate_plan()
    ↓
┌────────────────────────────────────┐
│ 1. ConstraintParser                │
│    - Parse dates, budget, style    │
│    - Validate constraints          │
│    - Generate assumptions          │
└───────────┬────────────────────────┘
            ↓
┌────────────────────────────────────┐
│ 2. DestinationRecommender          │
│    - Query GPT for destinations    │
│    - Score based on preferences    │
│    - Rank by match quality         │
└───────────┬────────────────────────┘
            ↓
    [Detail Level?]
            │
    ┌───────┴───────┬────────────────┐
    │               │                │
High Level      Medium           Full
    │               │                │
    ↓               ↓                ↓
Return         ItineraryPlanner   ItineraryPlanner
Destinations        ↓                ↓
                Return           DetailEnricher
                Outline              ↓
                                 Return Full
                                 Itinerary
                                     ↓
                              URL Validation
                                     ↓
                              Frontend Display
```

### I Have a Plan Flow (Dual-Model Enhancement)

```
User Input (Plan Mode)
    ↓
┌─────────────────────────────────────┐
│ • Existing plan text                │
│ • Destination                       │
│ • Action (enhance/modify/fill/opt)  │
│ • Optional: dates, budget, pace     │
└─────────────┬───────────────────────┘
              ↓
    POST /api/plan
              ↓
Orchestrator.enhance_existing_plan()
              ↓
┌─────────────────────────────────────┐
│ 1. ConstraintParser                 │
│    - Parse additional constraints   │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 2. PlanEnhancer (DUAL-MODEL)        │
│                                     │
│    ┌──────────────────────┐         │
│    │ HuggingFace Thread   │         │
│    │ (20s timeout)        │         │
│    │                      │         │
│    │ User Plan ──→ HF     │         │
│    │             Model    │         │
│    │              ↓       │         │
│    │          Insights    │         │
│    └──────────┬───────────┘         │
│               │                     │
│               ↓                     │
│    ┌──────────────────────┐         │
│    │ GPT-4 Enhancement    │         │
│    │                      │         │
│    │ User Plan ──┐        │         │
│    │             ├──→ GPT │         │
│    │ HF Insights ┘        │         │
│    │              ↓       │         │
│    │     Structured JSON  │         │
│    │     - Hotels         │         │
│    │     - Restaurants    │         │
│    │     - Timing         │         │
│    │     - Costs          │         │
│    │     - Tips           │         │
│    └──────────┬───────────┘         │
└───────────────┼─────────────────────┘
                ↓
         URL Validation
                ↓
        Frontend Display
        (Enhanced Plan)
```

### Agent Pipeline Details

```
┌──────────────────────────────────────────────────────────────┐
│                    ConstraintParser                           │
│  Input: Raw user data                                         │
│  Process:                                                     │
│    1. Parse dates → date range                                │
│    2. Normalize budget → daily budget                         │
│    3. Parse interests → list                                  │
│    4. Detect conflicts → warnings                             │
│    5. Fill gaps → assumptions                                 │
│  Output: Structured constraints object                        │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│              DestinationRecommender                           │
│  Input: Parsed constraints                                    │
│  Process:                                                     │
│    1. Build LLM prompt with constraints                       │
│    2. Query GPT-4 for recommendations                         │
│    3. Parse JSON response                                     │
│    4. Score destinations (0-100)                              │
│    5. Add distance/cost estimates                             │
│  Output: Ranked destination list                              │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│                 ItineraryPlanner                              │
│  Input: Top destination + constraints                         │
│  Process:                                                     │
│    1. Calculate trip duration                                 │
│    2. Build day-by-day structure                              │
│    3. Allocate activities by pace                             │
│    4. Add meal suggestions                                    │
│    5. Include transportation                                  │
│  Output: Day-by-day itinerary skeleton                        │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│                  DetailEnricher                               │
│  Input: Itinerary skeleton                                    │
│  Process:                                                     │
│    1. For each activity:                                      │
│       - Add specific timing                                   │
│       - Estimate costs                                        │
│       - Add booking info                                      │
│       - Include tips                                          │
│    2. Add hotel recommendations                               │
│    3. Add restaurant options                                  │
│    4. Include transport details                               │
│  Output: Fully detailed itinerary                             │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────────┐
│                 URLValidator                                  │
│  Input: Complete plan with URLs                               │
│  Process:                                                     │
│    1. Extract all URLs                                        │
│    2. Validate URL format                                     │
│    3. Check accessibility (optional)                          │
│    4. Filter invalid sources                                  │
│  Output: Validated plan                                       │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
              Frontend Display
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- OpenAI API key
- (Optional) HuggingFace token for dual-model enhancement

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy example file
cp .env.example .env

# Edit .env and add your API keys
OPENAI_API_KEY=your_openai_key_here
HF_TOKEN=your_huggingface_token_here  # Optional
```

4. Run the backend server:
```bash
python api.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open `http://localhost:3000` in your browser

## 📡 API Endpoints

### Core Endpoints

- **`POST /api/plan`** - Generate travel plan or enhance existing plan
  - **Discover Mode**: Provide preferences, get destination recommendations and itinerary
  - **Plan Mode**: Provide `existing_plan` + `specific_destination` for enhancement
  - Body: User constraints and preferences
  - Returns: Complete travel plan based on mode and detail level

- **`POST /api/refine`** - Refine existing plan
  - Body: `plan_id` and refinement parameters
  - Returns: Updated travel plan

- **`POST /api/alternatives`** - Get alternative destinations
  - Body: `plan_id` and count
  - Returns: Alternative destination recommendations

- **`GET /api/plan/<plan_id>`** - Retrieve specific plan
  - Returns: Previously generated plan

- **`GET /api/debug/<plan_id>`** - Get debug trace
  - Returns: Detailed execution trace for debugging

- **`POST /api/enrich/activity`** - Enrich single activity
  - Body: Activity details
  - Returns: Enriched activity with additional information

- **`POST /api/regenerate-day`** - Regenerate specific day
  - Body: `plan_id`, `day_number`, and adjustments
  - Returns: Updated plan with regenerated day

- **`POST /api/enrich-progressive`** - Progressive enrichment (streaming)
  - Body: Itinerary data
  - Returns: Server-Sent Events stream with progressive updates

### Utility Endpoints

- **`GET /`** - Health check
  - Returns: API status and version

## 💡 Usage Examples

### Discover Destinations Mode

```json
POST /api/plan
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

### I Have a Plan Mode (Enhancement)

```json
POST /api/plan
{
  "existing_plan": "Day 1: Arrive in Paris, check into hotel\nDay 2: Visit Eiffel Tower\nDay 3: Louvre Museum",
  "specific_destination": "Paris",
  "plan_action": "enhance",
  "dates": "2024-07-01 to 2024-07-07",
  "pace": "relaxed"
}
```

**Plan Actions:**
- `enhance` - Add timing, costs, tips (keep structure intact)
- `modify` - Improve and optimize activities
- `fill_gaps` - Add missing activities and details
- `optimize` - Reorganize for better flow

### Refine Existing Plan

```json
POST /api/refine
{
  "plan_id": "plan_abc123",
  "budget": 4000,
  "pace": "fast",
  "additional_interests": ["photography"]
}
```

## 🔧 Key Technologies

### Backend
- **Flask**: Web framework
- **OpenAI API (GPT-4o-mini)**: Primary LLM for planning
- **HuggingFace Transformers**: Secondary model for plan enhancement
  - Model: `Yanncccd/travel-agent-8b-v2`
- **Python 3.8+**: Core language
- **Requests**: HTTP library for web scraping
- **BeautifulSoup4**: HTML parsing for enrichment
- **PyTorch**: Deep learning framework for HF models

### Frontend
- **Next.js**: React framework with SSR
- **React**: UI library
- **CSS Modules**: Scoped styling
- **Fetch API**: Backend communication

## 🤖 Dual-Model Enhancement

The plan enhancement feature uses two AI models working together:

1. **HuggingFace Model** (travel-agent-8b-v2)
   - Provides travel-specific insights and suggestions
   - Runs with 20-second timeout for reliability
   - Generates natural language recommendations

2. **GPT-4 Model** (gpt-4o-mini)
   - Creates structured JSON output
   - Incorporates HF insights into comprehensive plan
   - Adds specific details (hotels, restaurants, costs, timing)

**Benefits:**
- Complementary strengths from both models
- Travel domain expertise + structured formatting
- Graceful fallback to GPT-only if HF times out

See `PLAN_ENHANCEMENT_CHANGES.md` for detailed documentation.

## 🧪 Testing

Run backend tests:
```bash
python test_backend.py
```

Run demo scripts:
```bash
cd backend
python demo.py
```

## 📊 Detail Levels

The system supports three detail levels in Discover mode:

1. **High-Level** (~20s): Destination recommendations only
2. **Medium** (~60s): Destination + basic itinerary outline  
3. **Full** (~90s): Complete itinerary with detailed activities, timing, and recommendations

Plan enhancement mode always provides full detail.

## 🔍 Debug Mode

Enable debug mode to see detailed traces of agent execution:

```json
{
  "debug_mode": true,
  ...other parameters
}
```

Debug traces include:
- Agent execution timing
- Intermediate outputs
- LLM prompt/response details
- Error traces
- Model usage (GPT vs Dual-model)

## 🛡️ Error Handling & Reliability

- **Timeout Protection**: HF model has 20-second timeout
- **Graceful Degradation**: Falls back to GPT-only if HF fails
- **JSON Parsing Fallbacks**: Multiple parsing strategies
- **URL Validation**: Filters invalid external sources
- **Retry Logic**: Automatic retries for transient failures
- **Debug Traces**: Comprehensive error logging

## 📝 License

MIT

## 🤝 Contributing

This is an academic project for Applied Machine Learning. For questions or issues, please contact the project team.

## 📚 Additional Documentation

- See `SETUP.md` for detailed setup instructions
- See `PLAN_ENHANCEMENT_CHANGES.md` for dual-model enhancement details
- See `architecture_diagram.html` for visual backend architecture flow
- Check individual agent files for implementation details

## 🎯 Project Highlights

- ✨ **Dual Planning Modes**: Discover new destinations or enhance existing plans
- 🤖 **Multi-Model AI**: Combines GPT-4 and HuggingFace for best results
- ⚡ **Progressive Refinement**: Iterative improvement of travel plans
- 🔒 **Robust & Reliable**: Timeout protection and graceful fallbacks
- 🎨 **Modern UI**: Clean, responsive React interface
- 📊 **Transparent**: Shows reasoning, assumptions, and warnings
- 🌐 **Production-Ready**: URL validation, error handling, debug mode
