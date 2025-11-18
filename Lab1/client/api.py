import requests

API_URL = "http://localhost:8000"


def get_books(title="", author=""):
    params = {"title": title, "author": author}
    r = requests.get(f"{API_URL}/books", params=params)
    data = r.json()

    if not data.get("books"):
        return {"too_many": True, "count": data.get("count", 0), "books": []}

    return {"too_many": False, "count": data.get("count", 0), "books": data["books"]}


def get_recommendations(book_id: int):
    r = requests.get(f"{API_URL}/recommend/{book_id}")
    return r.json()


def get_top_books(start_year=None, end_year=None, limit=50):
    params = {}
    if start_year is not None:
        params["start_year"] = start_year
    if end_year is not None:
        params["end_year"] = end_year
    if limit is not None:
        params["limit"] = limit
    r = requests.get(f"{API_URL}/top_books", params=params)
    return r.json()
