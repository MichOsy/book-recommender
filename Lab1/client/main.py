import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListWidget, QHeaderView,
    QPushButton, QLabel, QTabWidget, QLineEdit, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QSpinBox, QFormLayout
)
from PySide6.QtCore import QThread, Signal, QObject, QTimer, Qt
from api import get_books, get_recommendations, get_top_books


class RecWorker(QObject):
    finished = Signal(list)

    def __init__(self, book_id):
        super().__init__()
        self.book_id = book_id

    def run(self):
        recs = get_recommendations(self.book_id)
        self.finished.emit(recs)


class FilterWorker(QObject):
    finished = Signal(dict)

    def __init__(self, title, author):
        super().__init__()
        self.title = title
        self.author = author

    def run(self):
        result = get_books(title=self.title, author=self.author)
        self.finished.emit(result)


class TopWorker(QObject):
    finished = Signal(dict)

    def __init__(self, start_year, end_year, limit):
        super().__init__()
        self.start_year = start_year
        self.end_year = end_year
        self.limit = limit

    def run(self):
        result = get_top_books(start_year=self.start_year, end_year=self.end_year, limit=self.limit)
        self.finished.emit(result)


class ClientApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Book recommender")
        self.resize(800, 520)

        tabs = QTabWidget()
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tabs)

        # Recommendations tab
        tab_recs = QWidget()
        t2 = QVBoxLayout(tab_recs)

        filter_box = QHBoxLayout()

        self.filter_title = QLineEdit()
        self.filter_title.setPlaceholderText("Filter by title")
        self.filter_title.textChanged.connect(self.start_filter_timer)
        filter_box.addWidget(self.filter_title)

        self.filter_author = QLineEdit()
        self.filter_author.setPlaceholderText("Filter by author")
        self.filter_author.textChanged.connect(self.start_filter_timer)
        filter_box.addWidget(self.filter_author)
        t2.addLayout(filter_box)

        self.message_label = QLabel("Type a title or author to filter books and get recommendations")
        t2.addWidget(self.message_label)

        self.book_list = QTreeWidget()
        self.book_list.setColumnCount(2)
        self.book_list.setHeaderLabels(["Title", "Author"])
        header = self.book_list.header()
        header.setSectionResizeMode(QHeaderView.Interactive)  # noqa
        self.book_list.setColumnWidth(0, self.book_list.width() // 1.8)  # noqa
        self.book_list.setColumnWidth(1, self.book_list.width() // 2)
        t2.addWidget(self.book_list)

        self.btn = QPushButton("Recommend")
        self.btn.clicked.connect(self.recommend)
        t2.addWidget(self.btn)

        t2.addWidget(QLabel("Recommendations:"))
        self.recommend_list = QListWidget()
        t2.addWidget(self.recommend_list)

        tabs.addTab(tab_recs, "Recommendations")

        # Top books tab
        tab_top_books = QWidget()
        t_top = QVBoxLayout(tab_top_books)

        controls_layout = QHBoxLayout()
        form = QFormLayout()

        self.start_year_spin = QSpinBox()
        self.start_year_spin.setMinimum(0)
        self.start_year_spin.setMaximum(3000)
        self.start_year_spin.setValue(2000)
        form.addRow("Start year:", self.start_year_spin)

        self.end_year_spin = QSpinBox()
        self.end_year_spin.setMinimum(0)
        self.end_year_spin.setMaximum(3000)
        self.end_year_spin.setValue(2025)
        form.addRow("End year:", self.end_year_spin)

        self.limit_spin = QSpinBox()
        self.limit_spin.setMinimum(1)
        self.limit_spin.setMaximum(500)
        self.limit_spin.setValue(50)
        form.addRow("Top:", self.limit_spin)

        controls_layout.addLayout(form)
        self.top_refresh_btn = QPushButton("Refresh")
        self.top_refresh_btn.clicked.connect(self.load_top_books)
        controls_layout.addWidget(self.top_refresh_btn)
        t_top.addLayout(controls_layout)

        self.top_table = QTreeWidget()
        self.top_table.setColumnCount(4)
        self.top_table.setHeaderLabels(["Title", "Author(s)", "Rating", "Year"])

        top_header = self.top_table.header()
        top_header.setSectionResizeMode(QHeaderView.Interactive)  # noqa
        top_header.setStretchLastSection(True)

        self.top_table.setSortingEnabled(True)
        top_header.setSortIndicatorShown(True)
        top_header.setSectionsClickable(True)

        self.top_table.sortByColumn(2, Qt.DescendingOrder)  # noqa

        self.top_table.setColumnWidth(0, int(self.top_table.width() * 0.45))
        self.top_table.setColumnWidth(1, int(self.top_table.width() * 0.30))
        self.top_table.setColumnWidth(2, 80)
        self.top_table.setColumnWidth(3, 60)

        t_top.addWidget(self.top_table)

        t_top.addWidget(self.top_table)
        tabs.addTab(tab_top_books, "Top books")

        self.result = get_books()
        for b in self.result["books"]:
            item = QTreeWidgetItem([b["title"], b["authors"]])
            item.setData(0, Qt.UserRole, b["book_id"])  # noqa
            self.book_list.addTopLevelItem(item)

        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.run_filter)

        self.filter_title.textChanged.connect(self.start_filter_timer)
        self.filter_author.textChanged.connect(self.start_filter_timer)

        self.rec_thread = None
        self.rec_worker = None

        self.filter_thread = None
        self.filter_worker = None

        self.current_filter_id = 0

        self.load_top_books()

    def load_top_books(self):
        self.top_refresh_btn.setEnabled(False)
        self.top_table.clear()
        loading = QTreeWidgetItem(["Loading...", "", "", ""])
        self.top_table.addTopLevelItem(loading)

        start = self.start_year_spin.value()
        end = self.end_year_spin.value()
        limit = self.limit_spin.value()

        thread = QThread()
        worker = TopWorker(start, end, limit)
        worker.moveToThread(thread)

        def on_finished(result):
            self.top_table.clear()
            for b in result.get("books", []):
                year = b.get("original_publication_year")
                year_str = str(int(year)) if year not in (None, "") else ""
                rating = b.get("average_rating")
                rating_str = f"{float(rating):.2f}" if rating not in (None, "") else ""
                item = QTreeWidgetItem([b.get("title", ""), b.get("authors", ""), rating_str, year_str])
                item.setData(0, Qt.UserRole, b.get("book_id"))  # noqa
                self.top_table.addTopLevelItem(item)
            self.top_refresh_btn.setEnabled(True)
            worker.deleteLater()
            thread.quit()
            thread.wait()
            thread.deleteLater()

        thread.started.connect(worker.run)
        worker.finished.connect(on_finished)
        thread.start()

    def start_filter_timer(self):
        self.filter_timer.start(700)  # 700 ms debounce

    def run_filter(self):
        self.current_filter_id += 1
        filter_id = self.current_filter_id
        title_text = self.filter_title.text()
        author_text = self.filter_author.text()

        self.book_list.clear()
        self.message_label.setText("Loading...")

        thread = QThread()
        worker = FilterWorker(title_text, author_text)
        worker.moveToThread(thread)

        def on_finished(result):
            if filter_id == self.current_filter_id:
                self.update_filtered_books(result)
            worker.deleteLater()
            thread.quit()
            thread.wait()
            thread.deleteLater()

        thread.started.connect(worker.run)
        worker.finished.connect(on_finished)
        thread.start()

    def recommend(self):
        item = self.book_list.currentItem()
        if not item:
            self.recommend_list.clear()
            self.recommend_list.addItem("Please select a book from the list above to get recommendations")
            return

        book_id = item.data(0, Qt.UserRole)  # noqa

        self.recommend_list.clear()
        self.recommend_list.addItem("Loading...")

        self.rec_thread = QThread()
        self.rec_worker = RecWorker(book_id)
        self.rec_worker.moveToThread(self.rec_thread)

        self.rec_thread.started.connect(self.rec_worker.run)
        self.rec_worker.finished.connect(self.update_recommendations)
        self.rec_worker.finished.connect(self.rec_thread.quit)
        self.rec_worker.finished.connect(self.rec_worker.deleteLater)
        self.rec_thread.finished.connect(self.rec_thread.deleteLater)

        self.rec_thread.start()

    def update_recommendations(self, recs):
        self.recommend_list.clear()
        for r in recs:
            self.recommend_list.addItem(f"{r['title']} by {r['authors']}")

    def update_filtered_books(self, result):
        self.book_list.clear()

        title_text = self.filter_title.text().strip()
        author_text = self.filter_author.text().strip()

        if not title_text and not author_text:
            self.message_label.setText("Type a title or author to filter books and get recommendations")
            return

        if result["count"] == 0:
            self.message_label.setText("No matches found, refine your search")
            return

        if result["too_many"]:
            self.message_label.setText(f"Too many matches ({result['count']}), refine your search")
            return

        self.message_label.setText("")
        for b in result["books"]:
            item = QTreeWidgetItem([b["title"], b["authors"]])
            item.setData(0, Qt.UserRole, b["book_id"])  # noqa
            self.book_list.addTopLevelItem(item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ClientApp()
    window.show()
    sys.exit(app.exec())
