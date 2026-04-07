import re
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from vanna_setup import get_vanna_components
from vanna.core.llm import LlmRequest, LlmMessage
import plotly.express as px
import plotly.graph_objects as go

app = FastAPI(title="NL2SQL Clinic Agent API", version="1.0.0")

# Preload Vanna components
try:
    agent, memory, runner = get_vanna_components()
except Exception as e:
    print(f"Agent setup failed: {e}")
    agent, memory, runner = None, None, None

class ChatRequest(BaseModel):
    question: str

def validate_sql(sql: str) -> bool:
    """Blocks hazardous DML/DDL queries. Enforces SELECT/WITH only."""
    if not sql: return False
    sql_upper = sql.upper().strip()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")): return False
    blocked = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE"]
    for kw in blocked:
        if re.search(rf"\b{kw}\b", sql_upper): return False
    return True

@app.get("/health")
def health_check():
    """Basic service health check"""
    return {"status": "healthy" if agent else "degraded", "service": "NL2SQL API"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main Chat execution pipeline:
    Question -> Vanna Agent -> Validation -> SQLite Run -> Plotly Data -> Response
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    if not agent or not runner:
        raise HTTPException(status_code=500, detail="Vanna AI is not properly configured.")

    # 1. Ask Agent's LLM to generate SQL based on question
    try:
        from vanna.core.user.models import User
        dummy_user = User(id="default_user", email="test@example.com")
        
        prompt = f"Output ONLY a valid SQLite SELECT query based on this question: {request.question}"
        req = LlmRequest(user=dummy_user, messages=[LlmMessage(role="user", content=prompt)])
        llm_response = await agent.llm_service.send_request(req)
        sql_query = llm_response.content.replace("```sql", "").replace("```", "").strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")

    # 2. SQL Validation Layer check
    if not validate_sql(sql_query):
        raise HTTPException(status_code=403, detail="Invalid SQL: Only SELECT allowed.")

    # 3. SQLite DB Execution
    try:
        df = runner.run_sql(sql_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database execution error: {str(e)}")

    # Specific check for Empty Results
    if df.empty:
        return {
            "message": "Query executed successfully, but no matching results were found.",
            "sql": sql_query,
            "results": [],
            "chart": None
        }

    # 4. Chart Generation (Exec Python code locally)
    chart_json = None
    try:
        prompt_chart = f"Given a Pandas dataframe `df` with columns {list(df.columns)}, write Python code using `plotly.express` or `plotly.graph_objects` to create a chart `fig` (not returned, just assigned) for: '{request.question}'. Raw python only. Define `fig`."
        req_chart = LlmRequest(user=dummy_user, messages=[LlmMessage(role="user", content=prompt_chart)])
        resp_chart = await agent.llm_service.send_request(req_chart)
        plotly_code = resp_chart.content.replace("```python", "").replace("```", "").strip()
        
        local_env = {"df": df, "px": px, "go": go, "pd": pd}
        exec(plotly_code, {}, local_env)
        if "fig" in local_env:
            chart_json = json.loads(local_env["fig"].to_json())
    except Exception as e:
        print(f"Chart warning: {e}")

    # 5. Prepare Successful Response
    return {
        "message": "Query generated and executed successfully.",
        "sql": sql_query,
        "results": df.to_dict(orient="records"),
        "chart": chart_json
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)




