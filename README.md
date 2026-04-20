# NL2SQL Clinic Agent

An AI-powered Natural Language to SQL (NL2SQL) system designed for querying a Medical Clinic database using everyday language. This project leverages **Vanna AI**, **Google Gemini**, and **FastAPI** to securely translate questions into SQL queries, execute them on a live database, and generate visual charts (via **Plotly**) dynamically.

## 🚀 Features

- **Natural Language Parsing**: Ask questions like "How many appointments are scheduled for today?" and get real-time answers.
- **Robust Security**: Enforced SQL validation layer allows only safe `SELECT` statements, blocking hazardous DML/DDL queries.
- **Automatic Data Visualization**: Intelligent, on-the-fly generation of charts/graphs using Plotly express/graph_objects.
- **Context-Aware AI Memory**: Pre-seeded with curated Question-to-SQL pairs and schema context for significantly higher accuracy.
- **Synthesized Dataset**: Includes a script to generate a rich SQLite database (`clinic.db`) loaded with realistic, randomized fake medical data.

## 🏗️ Tech Stack

- **Framework**: `FastAPI` (with `uvicorn` for ASGI)
- **AI / LLM Integration**: `Vanna 2.x`, `Google Gemini`
- **Database**: `SQLite`
- **Data Manipulation & Visualization**: `Pandas`, `Plotly`
- **Mock Data Generation**: `Faker`

## 📁 Project Structure

- `setup_database.py`: Creates the realistic SQLite database (`clinic.db`) with tables for patients, doctors, appointments, treatments, and invoices using `Faker`.
- `vanna_setup.py`: Configures the Vanna AI agent, initializing the Gemini LLM service, memory module, and tools.
- `seed_memory.py`: Injects business logic, database schema documentation, and high-quality QA training data into the agent's memory to enhance SQL generation accuracy.
- `main.py`: Runs a FastAPI web server featuring a unified `/chat` API endpoint for natural language processing, validation, and chart generation.
- `requirements.txt`: Project dependencies list.
- `.env.example`: Template for environment variables.

## 🛠️ Usage & Setup Guide

### 1. Installation

First, clone the repository and set up a virtual environment.

```bash
python -m venv .venv
# Activate the virtual environment
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the `.env.example` file and configure your API key.

```bash
cp .env.example .env
```
Inside `.env`, set your **Google Gemini API Key**:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Initialize the Database and Memory

Generate the dummy SQLite database and populate Vanna Agent's knowledge base.

```bash
# Generates clinic.db
python setup_database.py

# Seeds the agent's memory with training pairs & schema
python seed_memory.py
```

### 4. Run the API Server

Start the FastAPI backend server:

```bash
python main.py
```
*Note: The server will be accessible locally at `http://127.0.0.1:8001`.*

## 🔌 API Documentation

### Health Check 
**GET `/health`**
Verifies the status of the fast API service and the availability of the Vanna AI agent.

### Chat Inference
**POST `/chat`**
Accepts a natural language query, performs SQL translation, checks for security, queries the database, generates a Plotly chart code, and responds.

**Request**
```json
{
  "question": "What are the top 5 most expensive treatments?"
}
```

**Successful Response**
```json
{
  "message": "Query generated and executed successfully.",
  "sql": "SELECT treatment_name, cost FROM treatments ORDER BY cost DESC LIMIT 5",
  "results": [
    {"treatment_name": "Surgery - Minor", "cost": 1500.0},
    {"treatment_name": "MRI Scan", "cost": 400.0}
  ],
  "chart": { /* JSON Representation of a Plotly figure */ }
}
```

If the SQL execution result is empty, the response will notify you appropriately but will gracefully handle the missing records without error.
