from fastapi import FastAPI, Query
from app.data_loader import load_books  # noqa
from app.recommender import BookRecommender  # noqa

app = FastAPI()

books = load_books()
recommender = BookRecommender(books)

MAX_RESULTS = 100


@app.get("/books")
def list_books(title: str = Query("", alias="title"), author: str = Query("", alias="author")):
    df = books
    if title:
        df = df[df["title"].str.contains(title, case=False)]
    if author:
        df = df[df["authors"].str.contains(author, case=False)]

    count = len(df)

    if count > MAX_RESULTS:
        return {"count": count, "books": []}

    return {"count": count, "books": df[["book_id", "title",
                                         "authors", "best_book_id"]].to_dict(orient="records")}


@app.get("/top_books")
def top_books(
    start_year: int = Query(None, alias="start_year"),
    end_year: int = Query(None, alias="end_year"),
    limit: int = Query(50, alias="limit")
):
    df = books

    if start_year:
        df = df[df["original_publication_year"] >= start_year]
    if end_year:
        df = df[df["original_publication_year"] <= end_year]

    df = df.sort_values(by="average_rating", ascending=False)
    df = df.head(min(limit, len(df)))

    return {"count": len(df),
            "books": df[["book_id", "title", "authors", "average_rating",
                         "original_publication_year", "best_book_id"]].to_dict(orient="records")}


@app.get("/recommend/{book_id}")
def recommend(book_id: int):
    return recommender.recommend_by_id(book_id)
