# Email Digest Agent & Content Intelligence Platform

## Project Overview
The **Email Digest Agent** is a comprehensive content intelligence platform designed to automate the consumption, analysis, and synthesis of high-signal information. It acts as a personal research assistant that aggregates data from newsletters, social discussions (Hacker News, Product Hunt), and video content (YouTube) to deliver actionable insights and identify viral market opportunities.

## Key Goals
- **Automated Curation:** Eliminate information overload by auto-summarizing newsletters and technical feeds.
- **Market Intelligence:** Identify underserved market needs ("pain points") by mining social discussions on Reddit and other platforms.
- **Strategic Briefings:** Transform fragmented data into structured daily briefs and weekly deep dives.
- **Trend Validation:** Cross-reference content with Google Trends to validate market interest.

## Architecture
The system follows a modern, decoupled architecture:

- **Frontend:** A responsive dashboard built with **Next.js** and **Tailwind CSS** for viewing briefs, deep dives, and discovery reports.
- **Backend:** A robust **Python** application using **FastAPI** for the API layer and **LangGraph** for orchestrating complex AI workflows.
- **Data Layer:** **PostgreSQL** for persistent storage of digests, emails, and opportunities, ensuring data integrity with upsert logic.
- **Infrastructure:** Fully containerized using **Docker** and **Docker Compose** for easy deployment and scaling.

## Tech Stack

### Frontend
- **Framework:** Next.js (React)
- **Styling:** Tailwind CSS
- **Visualization:** Custom components for displaying AI-generated insights

### Backend
- **Runtime:** Python 3.12+ (managed by `uv`)
- **API Framework:** FastAPI
- **AI Orchestration:** LangGraph (for Map-Reduce workflows and stateful agents)
- **LLM Integration:** OpenAI GPT models (via LangChain/LangGraph)

### Integrations
- **Gmail API:** For ingesting and analyzing newsletters.
- **Hacker News & Product Hunt APIs:** For tracking tech trends and launches.
- **YouTube Data API:** For video content summarization.
- **Google Trends:** For validating keyword popularity.

## Key Modules

### 1. Intelligent Email Processor
- **Daily Digest:** Summarizes general newsletters into categorized updates (Industry News, Tools, Insights).
- **Weekly Deep Dive:** specialized analysis for long-form essays, converting them into strategic briefings.
- **Parallel Processing:** Utilizes a Map-Reduce architecture to process multiple emails concurrently.

### 2. Viral App Discovery Engine
- **Purpose:** Identifies "Blue Ocean" opportunities by analyzing user complaints and requests.
- **Workflow:** A 4-phase process that:
    1. **Mines** pain points from Reddit, YouTube comments, and reviews.
    2. **Filters** for viability using LLMs.
    3. **Scores** opportunities based on potential impact.
    4. **Ranks** and presents the top ideas.

### 3. Multi-Source Aggregation
- **Product Hunt:** Daily and weekly analysis of top AI product launches.
- **Hacker News:** Sentiment analysis of top developer stories.
- **YouTube:** Summaries of videos from curated influencer channels.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- API Keys (OpenAI, Google Workspace, etc.)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd emailagent
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and populate your API keys.
   ```bash
   cp .env.example .env
   ```

3. **Start Services:**
   ```bash
   docker-compose up -d --build
   ```

4. **Access Dashboard:**
   Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
emailagent/
├── backend/               # Python processing engine & API
│   ├── api/               # FastAPI endpoints
│   ├── processor/         # LangGraph workflows (email, viral_app, etc.)
│   ├── sources/           # API clients (Gmail, HN, PH, YouTube)
│   └── main.py            # Entry point for processing jobs
├── dashboard/             # Next.js Frontend
│   ├── src/app/           # App router pages
│   └── src/components/    # UI components
└── docker-compose.yml     # Container orchestration
```
