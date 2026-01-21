# Media Monitoring Dashboard

## Overview

The **Media Monitoring Dashboard** is a web-based visualization interface designed to explore narrative intelligence derived from Indonesian news. It consumes data processed by the Media Pipeline, offering insights into entity sentiment, dominant phrases, and co-occurrence networks.

The dashboard runs as a **single-page application (SPA)** served by a **FastAPI** backend. It uses **Bootstrap 5** for layout and **D3.js** for high-performance visualizations.

---

## Features

### 1. Weekly Sentiment Trend
- **Visualization**: Multi-line chart tracking sentiment (Positive, Neutral, Negative) over the last 7 days.
- **Interaction**: 
  - Dynamic scaling based on selected date range.
  - Hover tooltips for precise daily counts.
- **Design**: Uses straight linear interpolation for precise tracking.

### 2. Dominant Phrases
- **Visualization**: A responsive table listing the most frequent phrases surrounding the searched entity.
- **Interaction**:
  - Pagination to explore more phrases.
  - "Count" column visualizes framing frequency.
- **Design**: Clean, light-themed rows with truncated text handling and fixed layout stability.

### 3. Co-occurrence Network
- **Visualization**: Force-directed graph showing relationships between entities.
- **Nodes**: Entities (Person, Org, Location, etc.) sized by article volume.
- **Links**: Connections represent co-occurrnece in the same articles.
- **Interaction**:
  - **Drag**: Rearrange nodes layout.
  - **Click**: Highlight a node and its direct connections (egocentric view).
  - **Zoom/Pan**: Explore large networks.
  - **Legend**: Color-coded by entity type (PER, ORG, GPE, etc.).

### 4. Advanced Filtering (Side Panel)
- **Search**: Query any entity (e.g., "Jokowi", "KPU").
- **Date Range**: Filter data down to specific days.
- **NER Score**: Adjust confidence threshold (0.0 - 1.0) to filter noisy entities.
- **Entity Types**: Toggle specific categories (PER, ORG, LAW, etc.) to refine the network.
- **Network Filters**:
  - **Show/Hide Searched Entity**: Toggle the central node to declutter the graph.
  - **Exclude Entities**: Add specific terms (e.g., "wapres") to remove them from analysis.

---

## Technical Architecture

### Frontend (`web/`)
- **Structure**:
  - `index.html`: Main entry point, layout structure.
  - `css/style.css`: Custom styles and Bootstrap overrides (Light Theme).
  - `js/main.js`: Application logic (event listeners, state management).
  - `js/api.js`: API client wrapper.
  - `js/charts/*.js`: D3.js visualization modules (trend, phrases, network).

- **Frameworks**:
  - **Bootstrap 5**: Responsive grid, components (Offcanvas, Cards, Modals).
  - **D3.js (v7)**: Drawing SVG charts and handling simulation physics.

### Backend (`api/`)
- **Framework**: **FastAPI** (Python).
- **Function**: Serves static files and provides REST endpoints for data.
- **Endpoints**:
  - `GET /api/trends`: returns aggregations of daily sentiment.
  - `GET /api/phrases`: returns top n-gram phrases using framing analysis.
  - `GET /api/network`: returns nodes and links for force-directed graph.
  - `GET /`: returns the main dashboard HTML.

---

## How to Run

1. **Activate Environment**:
   Ensure you are in the project root and virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. **Start Server**:
   Run the FastAPI server using Uvicorn:
   ```bash
   ./venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access Dashboard**:
   Open browser at [http://localhost:8000](http://localhost:8000).

---

## Usage Guide

1. **Search**: Enter an entity name in the side panel search bar (e.g., "Prabowo").
2. **Analyze**: Click "Analyze" to fetch data.
3. **Refine**:
   - Use the **Exclude Entities** input to remove specific noisy nodes (e.g., generic terms like "jakarta").
   - Adjust **NER Score** slider if you see too many irrelevant entities.
   - Use **Date Range** to narrow down to a specific event window.
4. **Interact**: Click nodes in the network graph to focus on their connections.
