import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_books():
    books = pd.read_csv(DATA_DIR / "books.csv")
    tags = pd.read_csv(DATA_DIR / "tags.csv")
    book_tags = pd.read_csv(DATA_DIR / "book_tags.csv")

    merged = book_tags.merge(tags, on="tag_id", how="left")
    grouped_tags = merged.groupby("goodreads_book_id")["tag_name"].apply(lambda x: " ".join(x))

    books = books.merge(grouped_tags, left_on="id", right_index=True, how="left")

    books["text"] = (
        books["title"].fillna("") + " " +
        books["authors"].fillna("") + " " +
        books["tag_name"].fillna("")
    )

    return books


if __name__ == "__main__":
    books_ = load_books()
    # print(books["isbn13"])
    # print((books["isbn13"] == '').sum())
