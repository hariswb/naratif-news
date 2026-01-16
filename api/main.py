from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from pipeline.db import get_db_session
from api.queries import get_trends_data, get_framing_data, get_network_data

app = FastAPI()

# Dependency
def get_db():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()

class TrendPoint(BaseModel):
    date: str
    label: str
    count: int

class PhrasePoint(BaseModel):
    phrase: str
    count: int

class NetworkNode(BaseModel):
    id: str
    group: str
    count: int

class NetworkLink(BaseModel):
    source: str
    target: str
    value: int

class NetworkGraph(BaseModel):
    nodes: List[NetworkNode]
    links: List[NetworkLink]

def _get_date_range(start_date: Optional[str], end_date: Optional[str]):
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
    else:
        end_dt = datetime.now()
        
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
    else:
        start_dt = end_dt - timedelta(days=7)
    return start_dt, end_dt

@app.get("/api/trends")
def get_trends(
    entity: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    start_dt, end_dt = _get_date_range(start_date, end_date)
    
    result = get_trends_data(db, entity, start_dt, end_dt)
    
    data = []
    for row in result:
        data.append({
            "date": row.published_date.isoformat(),
            "label": row.label,
            "count": row.count
        })
    return data

@app.get("/api/phrases")
def get_phrases(
    entity: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    start_dt, end_dt = _get_date_range(start_date, end_date)
    
    result = get_framing_data(db, entity, start_dt, end_dt)
    
    data = [{"phrase": row.framing_phrase, "count": row.count} for row in result]
    return data

@app.get("/api/network")
def get_network(
    entity: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_score: float = 0.0,
    max_score: float = 1.0,
    groups: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    start_dt, end_dt = _get_date_range(start_date, end_date)
    
    nodes_result, links_result = get_network_data(db, entity, start_dt, end_dt, min_score, max_score, groups)
    
    nodes = []
    for row in nodes_result:
        nodes.append({
            "id": row.word,
            "group": "SEARCHED" if row.word.lower() == entity.lower() else row.entity_group,
            "count": row.count
        })
        
    links = []
    for row in links_result:
        links.append({
            "source": row.source,
            "target": row.target,
            "value": row.value
        })
    
    return {"nodes": nodes, "links": links}

# Mount static files – MUST BE LAST to not block API routes
app.mount("/", StaticFiles(directory="web", html=True), name="static")
