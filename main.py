from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "NewsRAG API running"}

@app.post("/update-news")
def update_news():
    return {"status": "OK", "message": "News update placeholder"}

@app.post("/query")
def query_news(query: str):
    return {"query": query, "answer": "Sample response"}


