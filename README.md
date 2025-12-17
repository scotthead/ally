# Ally - AI-Powered Product Optimization System

## Product Description

Ally is an AI-powered system designed to help optimize product listings by analyzing competitive products and providing actionable recommendations. The system uses Google's Gemini LLM to generate comprehensive competitive analysis reports and product improvement recommendations based on Amazon's product listing guidelines.

1. [Call Flow](#call-flow)
1. [Setup Instructions](#env-setup) 
1. [Assumptions](#assumptions)
1. [Limitations](#limitations)
1. [Project Structure](#structure)

## <a name="call-flow"></a>Call Flow

The application follows a three-page workflow:

1. **Products Page** (`http://localhost:8000/`)
   - Displays a list of all products loaded from the CSV file
   - Each product has a "Start Competitive Analysis" button
   - Optional "Disable Cached Values" checkbox to force regeneration of reports
   - "View Last Updates" button to see the summary of previously applied recommendations

2. **Recommendations Page** (`http://localhost:8000/recommendations/{product_id}/`)
   - Shows AI-generated competitive analysis and recommendations for improving the product listing
   - Recommendations are based on competitive analysis and Amazon guidelines
   - User can review recommendations before accepting or rejecting
   - "Accept Recommendations" button initiates the product update process
   - "Reject Recommendations" button takes the user back to the products page

3. **Summary Page** (`http://localhost:8000/summary/{product_id}/`)
   - Shows a comprehensive summary of all changes applied to the product
   - Details what was updated (title, description, category, brand, bullet points)

**Important**: User approval is required to apply recommendations. Changes are not made to the product until the user clicks "Accept Recommendations" on the recommendations page.

## Agents

The system uses multiple AI agents powered by Google's Gemini model:

### 1. Competitive Report Agent
**Purpose**: Analyzes the product against competitor products to identify strengths, weaknesses, and opportunities.

**Location**: `ally/ai/agents/competitor_report/`

**Instructions**: [competitor_report/prompt.py](ally/ai/agents/competitor_report/prompt.py)

**Output**: Generates a markdown report saved to `reports/competitive_report_{product_id}.md`

### 2. Recommendations Agent
**Purpose**: Reviews the competitive analysis report and generates specific, actionable recommendations for improving the product listing based on Amazon guidelines.

**Location**: `ally/ai/agents/recommendations/`

**Instructions**: [recommendations/prompt.py](ally/ai/agents/recommendations/prompt.py)

**Output**: Generates a markdown report saved to `recommendations/recommendations_{product_id}.md`

### 3. Final Agent (Sequential Agent)
**Purpose**: Orchestrates the application of approved recommendations by coordinating multiple sub-agents.

**Location**: `ally/ai/agents/finalize/`

**Sub-agents**:
- **Update Product Agent (3 instances)**: Applies specific product updates based on recommendations
  - **Location**: `ally/ai/agents/finalize/subagents/update/`
  - **Instructions**: [finalize/subagents/update/prompt.py](ally/ai/agents/finalize/subagents/update/prompt.py)
  - **Tools**: Can update title, description, category, brand, and bullet points

- **Summarization Agent**: Creates a comprehensive summary of all changes applied
  - **Location**: `ally/ai/agents/finalize/subagents/summarize/`
  - **Instructions**: [finalize/subagents/summarize/prompt.py](ally/ai/agents/finalize/subagents/summarize/prompt.py)
  - **Output**: Generates a markdown summary saved to `summarization/summary_{product_id}.md`

## Agent Call Flow Interaction

1. **User clicks "Start Competitive Analysis"** on Products Page
   - Triggers `Competitive Report Agent`
   - Agent analyzes product vs competitors
   - Report cached in `CompetitorReportService`
   - System automatically triggers `Recommendations Agent`
   - Recommendations cached in `ProductRecommendationService`
   - User redirected to Recommendations Page

2. **User reviews recommendations** on Recommendations Page
   - User can read AI-generated competitive analysis and recommendations
   - User clicks "Accept Recommendations" when satisfied

3. **User accepts recommendations** on Recommendations Page
   - Triggers `Final Agent` (SequentialAgent)
   - Three `Update Product Agents` run sequentially to apply changes
   - Each agent reads recommendations and updates specific product fields
   - Changes are persisted to CSV file
   - `Summarization Agent` generates final summary
   - Summary cached in `SummarizationService`
   - User redirected to Summary Page

4. **User views summary** on Summary Page
   - Displays comprehensive report of all changes
   - User clicks "OK" to return to Products Page

## <a name="env-setup"></a>Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Google API key with access to Gemini

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:scotthead/ally.git
   cd ally
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the project root directory (same location as `manage.py`):
   ```bash
   # Required: Google API Key for Gemini
   GOOGLE_API_KEY=your-google-api-key-here

   # Optional: Override default file paths
   # PRODUCTS_FILE=/path/to/products.csv
   # COMPETITORS_FILE=/path/to/competitors.csv

   # Optional: Django settings
   # SECRET_KEY=your-secret-key-here
   # DEBUG=True
   ```

   Replace `your-google-api-key-here` with your actual Google API key that has access to the Gemini model.

4. **Start the development server**
   ```bash
   python manage.py runserver
   ```

5. **Access the application**

   Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

   You should see the Products page with a list of all available products.

## <a name="assumptions"></a>Assumptions

1. **LLM Model**: The system uses Google's Gemini model as the primary language model for all AI operations (competitive analysis, recommendations, and product updates).

2. **Synthetic Competitor Data**: The competitor products in the system are synthetic products that were generated using Gemini by taking existing products and creating realistic competitor variations. This approach was necessary because all existing Amazon product APIs that were found required payment or had restrictive access requirements.

3. **Verbose Logging**: Since this was a prototype, verbose logging was added to the system and specifically to the agents to allow for a better view of the interactions and to help debug the system.

## <a name="limitations"></a>Limitations

1. **Separate Agent Workflow**: Due to time constraints, the competitive report generation and recommendations generation are separate sequential steps. With more time, these could be combined into a single, more efficient workflow that generates both outputs in one pass.

2. **File Storage**: Product data, competitor data, and AWS guidelines are stored in CSV and text files rather than the database. This limits query performance and makes concurrent access more difficult. This was done to save time.

3. **AWS Guidelines Processing**: The system loads AWS product listing guidelines from text files and passes them directly to the AI agents. With more time, the guidelines would be processed and stored in a vector database (such as Pinecone) to enable semantic search. This would allow the agents to retrieve only the most relevant guidelines for each specific product category and recommendation type, improving both accuracy and performance.

4. **No Image Analysis**: Product images are ignored in the analysis pipeline. A more complete system would analyze product images and competitor images to provide visual optimization recommendations.

5. **Limited Error Handling**: Error handling is basic and could be improved with retry logic, better error messages, and graceful degradation when services are unavailable.

6. **No User Authentication**: The system does not include user authentication or authorization. All users have full access to view and modify all products.

## <a name="structure"></a>Project Structure

```
ally/
├── ally/                          # Main Django app
│   ├── ai/
│   │   └── agents/               # AI agent implementations
│   │       ├── competitor_report/    # Competitive analysis agent
│   │       ├── recommendations/      # Recommendations agent
│   │       └── finalize/            # Final agent and sub-agents
│   ├── data/                     # CSV data files
│   ├── management/
│   │   └── commands/            # Django management commands
│   ├── services/                # Service layer (caching, persistence)
│   ├── templates/               # HTML templates
│   └── views.py                 # Django views
├── config/                       # Django configuration
├── reports/                      # Generated competitive reports
├── recommendations/              # Generated recommendations
├── summarization/               # Generated summaries
├── .env                         # Environment variables (not in git)
├── manage.py                    # Django management script
└── requirements.txt             # Python dependencies
```
