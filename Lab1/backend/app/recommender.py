from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BookRecommender:
    def __init__(self, books_df):
        self.books = books_df

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.books["text"])

    def recommend_by_id(self, book_id, top_n=10):
        target_idx = self.books.index[self.books["book_id"] == book_id]
        if len(target_idx) == 0:
            return []

        target_idx = target_idx[0]

        similarities = cosine_similarity(
            self.matrix[target_idx],
            self.matrix
        ).flatten()

        similar_indices = similarities.argsort()[::-1][1:top_n+1]

        results = self.books.iloc[similar_indices][["book_id", "title", "authors", "best_book_id"]]

        return results.to_dict(orient="records")


if __name__ == "__main__":
    from data_loader import load_books
    books = load_books()
    rec = BookRecommender(books)
    print(rec.recommend_by_id(books["book_id"][123]))
