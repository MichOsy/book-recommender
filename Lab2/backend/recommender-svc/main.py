from fastapi import FastAPI
from data_loader import load_books
from recommender import BookRecommender

app = FastAPI()

books = load_books()
rec = BookRecommender(books)


@app.get("/recommend/{book_id}")
def recommend(book_id: int):
    return rec.recommend_by_id(book_id)
