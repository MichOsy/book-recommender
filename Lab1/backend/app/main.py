from fastapi import FastAPI
from app.data_loader import load_books  # noqa
from app.recommender import BookRecommender  # noqa

app = FastAPI()

books = load_books()
recommender = BookRecommender(books)


@app.get("/books")
def list_books():
    return books[["book_id", "title"]].head(50).to_dict(orient="records")


@app.get("/recommend/{book_id}")
def recommend(book_id: int):
    return recommender.recommend_by_id(book_id)
