from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# 環境変数ロード
load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

app = FastAPI(title="NewsRAG Backend (GNews Version)")

# --- Firebase 初期化 ---
cred_path = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_admin._apps:
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        raise RuntimeError("Firebase credentials file not found.")

db = firestore.client()

# --- Pydantic モデル ---
class NewsRequest(BaseModel):
    categories: list[str] = ["technology", "science", "business"]


@app.post("/update-news")
def update_news(req: NewsRequest):
    """
    GNews APIからカテゴリ別ニュースを取得し、Firestoreに保存
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

        res = requests.get(base_url, params=params)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)

        data = res.json()

        for article in data.get("articles", []):
            # --- Firestore登録用オブジェクト ---
            article_obj = {
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

            # --- Firestoreに保存（URLをドキュメントIDに） ---
            if article_obj["url"]:
                doc_id = article_obj["url"].replace("/", "_")
                db.collection("news").document(doc_id).set(article_obj)
                all_articles.append(article_obj)

    return {
        "status": "success",
        "count": len(all_articles),
        "articles": all_articles[:5],
    }
