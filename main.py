from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数ロード
load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

app = FastAPI(title="NewsRAG Backend (GNews Version)")

# --- Pydantic モデル ---
class NewsRequest(BaseModel):
    categories: list[str] = ["technology", "science", "business"]


@app.post("/update-news")
def update_news(req: NewsRequest):
    """
    GNews APIからカテゴリ別ニュースを取得
    """
    if not GNEWS_API_KEY:
        raise HTTPException(status_code=500, detail="GNEWS_API_KEY not found")

    all_articles = []
    base_url = "https://gnews.io/api/v4/top-headlines"

    for category in req.categories:
        params = {
            "topic": category,
            "lang": "en",
            "country": "us",
            "max": 10,
            "apikey": GNEWS_API_KEY,
        }

        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        for article in data.get("articles", []):
            news = {
                "title": article.get("title"),
                "description": article.get("description"),
                "content": article.get("content"),
                "url": article.get("url"),
                "image": article.get("image"),
                "publishedAt": article.get("publishedAt"),
                "source": article.get("source", {}).get("name"),
                "category": category,
                "retrievedAt": datetime.utcnow().isoformat(),
            }
            all_articles.append(news)

    return {
        "status": "success",
        "count": len(all_articles),
        "articles": all_articles[:5],
    }
