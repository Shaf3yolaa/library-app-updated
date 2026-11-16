import os
import uuid
from decimal import Decimal, InvalidOperation

import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "super-secret-key")
bcrypt = Bcrypt(app)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024

def get_library_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database="library",
        cursorclass=pymysql.cursors.DictCursor,
    )


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def save_image(file_storage, folder):
    if not file_storage or not file_storage.filename:
        return None, None
    if not allowed_image(file_storage.filename):
        return None, "Please upload a PNG, JPG, JPEG, WEBP, or GIF image."
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_IMAGE_SIZE:
        return None, "Image size must be 5 MB or less."

    ext = secure_filename(file_storage.filename).rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(app.static_folder, "uploads", folder)
    os.makedirs(upload_dir, exist_ok=True)
    file_storage.save(os.path.join(upload_dir, filename))
    return f"uploads/{folder}/{filename}", None


def delete_image(image_path):
    if not image_path:
        return
    safe_path = os.path.normpath(image_path).replace("\\", "/")
    if safe_path.startswith("uploads/"):
        full_path = os.path.join(app.static_folder, safe_path)
        if os.path.isfile(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass


def book_form_options(cursor):
    """Lists used by the add/edit book forms (author, publisher, category)."""
    cursor.execute("SELECT author_id, name FROM AUTHOR ORDER BY name;")
    authors = cursor.fetchall()
    cursor.execute("SELECT publisher_id, name FROM PUBLISHER ORDER BY name;")
    publishers = cursor.fetchall()
    cursor.execute("SELECT category_id, name FROM CATEGORY ORDER BY name;")
    categories = cursor.fetchall()
    return authors, publishers, categories

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("library"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = {"name": "", "email": "", "password": "", "confirm_password": ""}
    if request.method == "POST":
        form = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "password": request.form.get("password", ""),
            "confirm_password": request.form.get("confirm_password", ""),
        }

        error = None
        if not form["name"]:
            error = "Name is required"
        elif not form["email"]:
            error = "Email is required"
        elif not form["password"]:
            error = "Password is required"
        elif not form["confirm_password"]:
            error = "Confirm password is required"
        elif form["password"] != form["confirm_password"]:
            error = "Passwords do not match"

        if error:
            flash(error, "error")
            return render_template("register.html", form=form)

        pw_hash = bcrypt.generate_password_hash(form["password"]).decode("utf-8")
        conn = get_library_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s);",
                    (form["email"], form["name"], pw_hash),
                )
                user_id = cursor.lastrowid
            conn.commit()
            session["user_id"] = user_id
            session["name"] = form["name"]
            return redirect(url_for("library"))
        except pymysql.err.IntegrityError:
            conn.rollback()
            flash("Email already exists", "error")
            return render_template("register.html", form=form)
        finally:
            conn.close()

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email:
            flash("Email is required", "error")
        elif not password:
            flash("Password is required", "error")
        else:
            conn = get_library_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT user_id, name, password_hash FROM users WHERE email = %s;", (email,))
                    user = cursor.fetchone()
                if user and bcrypt.check_password_hash(user["password_hash"], password):
                    session["user_id"] = user["user_id"]
                    session["name"] = user["name"]
                    return redirect(url_for("library"))
                flash("Invalid email or password", "error")
            finally:
                conn.close()
    return render_template("login.html", email=email)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/library")
def library():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_library_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM AUTHOR ORDER BY name;")
            authors = cursor.fetchall()

            cursor.execute("SELECT * FROM BOOK ORDER BY title;")
            books = cursor.fetchall()

            for book in books:
                cursor.execute(
                    "SELECT name FROM AUTHOR WHERE author_id = %s;",
                    (book["author_id"],)
                )
                author = cursor.fetchone()

                book["author_name"] = (
                    author["name"] if author else "Unknown"
                )

    finally:
        conn.close()

    return render_template(
        "library.html",
        authors=authors,
        books=books
    )



@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    if "user_id" not in session:
        return redirect(url_for("login"))
    form = {"name": "", "country": ""}
    if request.method == "POST":
        form = {"name": request.form.get("name", "").strip(), "country": request.form.get("country", "").strip()}
        image_path, image_error = save_image(request.files.get("image"), "authors")
        if not form["name"] or not form["country"]:
            if image_path: delete_image(image_path)
            flash("Please complete all author fields.", "error")
            return render_template("add_author.html", form=form)
        if image_error:
            flash(image_error, "error")
            return render_template("add_author.html", form=form)
        conn = get_library_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO AUTHOR (name, country, image_path) VALUES (%s, %s, %s);", (form["name"], form["country"], image_path))
            conn.commit()
        finally:
            conn.close()
        flash("Author added successfully!", "success")
        return redirect(url_for("library"))
    return render_template("add_author.html", form=form)


@app.route("/edit_author/<int:author_id>", methods=["GET", "POST"])
def edit_author(author_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM AUTHOR WHERE author_id = %s;", (author_id,))
            author = cursor.fetchone()
        if not author:
            flash("Author not found.", "error")
            return redirect(url_for("library"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            country = request.form.get("country", "").strip()
            new_image, image_error = save_image(request.files.get("image"), "authors")
            if not name or not country:
                if new_image: delete_image(new_image)
                flash("Please complete all author fields.", "error")
                return render_template("edit_author.html", author={**author, "name": name, "country": country})
            if image_error:
                flash(image_error, "error")
                return render_template("edit_author.html", author={**author, "name": name, "country": country})
            image_path = new_image if new_image else author.get("image_path")
            with conn.cursor() as cursor:
                cursor.execute("UPDATE AUTHOR SET name=%s, country=%s, image_path=%s WHERE author_id=%s;", (name, country, image_path, author_id))
            conn.commit()
            if new_image and author.get("image_path"):
                delete_image(author["image_path"])
            flash("Author updated successfully!", "success")
            return redirect(url_for("library"))
    finally:
        conn.close()
    return render_template("edit_author.html", author=author)


@app.route("/delete_author/<int:author_id>", methods=["POST"])
def delete_author(author_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    image_paths = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT image_path FROM AUTHOR WHERE author_id=%s;", (author_id,))
            author = cursor.fetchone()
            cursor.execute("SELECT image_path FROM BOOK WHERE author_id=%s;", (author_id,))
            image_paths = [r["image_path"] for r in cursor.fetchall()]
            if author: image_paths.append(author.get("image_path"))
            cursor.execute("DELETE FROM AUTHOR WHERE author_id = %s;", (author_id,))
        conn.commit()
    finally:
        conn.close()
    for path in image_paths: delete_image(path)
    flash("Author and associated books deleted successfully!", "success")
    return redirect(url_for("library"))


BOOK_FORM_FIELDS = ("title", "price", "publish_year", "author_id", "publisher_id", "category_id")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if "user_id" not in session:
        return redirect(url_for("login"))
    form = {field: "" for field in BOOK_FORM_FIELDS}
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            authors, publishers, categories = book_form_options(cursor)
        if request.method == "POST":
            form = {field: request.form.get(field, "").strip() for field in BOOK_FORM_FIELDS}
            image_path, image_error = save_image(request.files.get("image"), "books")
            if not all(form.values()):
                if image_path: delete_image(image_path)
                flash("Please complete all book fields.", "error")
                return render_template("add_book.html", authors=authors, publishers=publishers, categories=categories, form=form)
            if image_error:
                if image_path: delete_image(image_path)
                flash(image_error, "error")
                return render_template("add_book.html", authors=authors, publishers=publishers, categories=categories, form=form)
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO BOOK (title, price, publish_year, author_id, publisher_id, category_id, image_path) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s);",
                    (form["title"], form["price"], form["publish_year"], form["author_id"],
                     form["publisher_id"], form["category_id"], image_path),
                )
            conn.commit()
            flash("Book added successfully!", "success")
            return redirect(url_for("library"))
    finally:
        conn.close()
    return render_template("add_book.html", authors=authors, publishers=publishers, categories=categories, form=form)


@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM BOOK WHERE book_id = %s;", (book_id,))
            book = cursor.fetchone()
            authors, publishers, categories = book_form_options(cursor)
        if not book:
            flash("Book not found.", "error")
            return redirect(url_for("library"))
        if request.method == "POST":
            values = {field: request.form.get(field, "").strip() for field in BOOK_FORM_FIELDS}
            new_image, image_error = save_image(request.files.get("image"), "books")
            if not all(values.values()):
                if new_image: delete_image(new_image)
                flash("Please complete all book fields.", "error")
                return render_template("edit_book.html", book={**book, **values}, authors=authors, publishers=publishers, categories=categories)
            if image_error:
                if new_image: delete_image(new_image)
                flash(image_error, "error")
                return render_template("edit_book.html", book={**book, **values}, authors=authors, publishers=publishers, categories=categories)
            image_path = new_image if new_image else book.get("image_path")
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE BOOK SET title=%s, price=%s, publish_year=%s, author_id=%s, publisher_id=%s, "
                    "category_id=%s, image_path=%s WHERE book_id=%s;",
                    (values["title"], values["price"], values["publish_year"], values["author_id"],
                     values["publisher_id"], values["category_id"], image_path, book_id),
                )
            conn.commit()
            if new_image and book.get("image_path"):
                delete_image(book["image_path"])
            flash("Book updated successfully!", "success")
            return redirect(url_for("library"))
    finally:
        conn.close()
    return render_template("edit_book.html", book=book, authors=authors, publishers=publishers, categories=categories)


@app.route("/delete_book/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    image_path = None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT image_path FROM BOOK WHERE book_id=%s;", (book_id,))
            book = cursor.fetchone()
            image_path = book.get("image_path") if book else None
            cursor.execute("DELETE FROM BOOK WHERE book_id = %s;", (book_id,))
        conn.commit()
    finally:
        conn.close()
    delete_image(image_path)
    flash("Book removed successfully!", "success")
    return redirect(url_for("library"))

@app.route("/search_books")
def search_books():
    if "user_id" not in session:
        return redirect(url_for("login"))

    keyword = request.args.get("keyword", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    category_id = request.args.get("category_id", "").strip()

    # Every user value is sent as a placeholder, never concatenated into the SQL
    filters = []
    params = []

    if keyword:
        filters.append("b.title LIKE %s")
        params.append(f"%{keyword}%")

    for column, label, raw in (("b.price >= %s", "Minimum price", min_price),
                               ("b.price <= %s", "Maximum price", max_price)):
        if not raw:
            continue
        try:
            value = Decimal(raw)
        except InvalidOperation:
            flash(f"{label} must be a number.", "error")
            continue
        if not value.is_finite() or value < 0:
            flash(f"{label} must be a positive number.", "error")
            continue
        filters.append(column)
        params.append(value)

    if category_id:
        try:
            filters.append("b.category_id = %s")
            params.append(int(category_id))
        except ValueError:
            flash("Unknown category.", "error")

    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT category_id, name FROM CATEGORY ORDER BY name;")
            categories = cursor.fetchall()

            sql = (
                "SELECT b.book_id, b.title, b.price, b.publish_year, "
                "       a.name AS author_name, p.name AS publisher_name, c.name AS category_name "
                "FROM BOOK b "
                "     JOIN AUTHOR a    ON a.author_id = b.author_id "
                "     JOIN PUBLISHER p ON p.publisher_id = b.publisher_id "
                "     JOIN CATEGORY c  ON c.category_id = b.category_id"
            )
            if filters:
                sql += " WHERE " + " AND ".join(filters)
            sql += " ORDER BY b.price ASC, b.title ASC;"
            cursor.execute(sql, params)
            books = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "search_books.html",
        books=books,
        categories=categories,
        keyword=keyword,
        min_price=min_price,
        max_price=max_price,
        category_id=category_id,
        searched=bool(request.args),
    )


@app.route("/catalogue")
def catalogue():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT b.book_id, b.title, b.price, b.publish_year, "
                "       a.name AS author_name, p.name AS publisher_name, c.name AS category_name "
                "FROM BOOK b "
                "     JOIN AUTHOR a    ON a.author_id = b.author_id "
                "     JOIN PUBLISHER p ON p.publisher_id = b.publisher_id "
                "     JOIN CATEGORY c  ON c.category_id = b.category_id "
                "ORDER BY a.name ASC, b.title ASC;"
            )
            books = cursor.fetchall()
    finally:
        conn.close()
    return render_template("catalogue.html", books=books)


@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT c.name AS category_name, COUNT(b.book_id) AS book_count, AVG(b.price) AS average_price "
                "FROM CATEGORY c JOIN BOOK b ON b.category_id = c.category_id "
                "GROUP BY c.category_id, c.name "
                "ORDER BY book_count DESC, c.name ASC;"
            )
            category_stats = cursor.fetchall()

            cursor.execute(
                "SELECT a.name AS author_name, COUNT(b.book_id) AS book_count "
                "FROM AUTHOR a JOIN BOOK b ON b.author_id = a.author_id "
                "GROUP BY a.author_id, a.name "
                "HAVING COUNT(b.book_id) >= 2 "
                "ORDER BY book_count DESC, a.name ASC;"
            )
            productive_authors = cursor.fetchall()

            cursor.execute(
                "SELECT COUNT(book_id) AS book_count, SUM(price) AS total_price, "
                "       MIN(price) AS smallest_price, MAX(price) AS largest_price FROM BOOK;"
            )
            library_totals = cursor.fetchone()
    finally:
        conn.close()
    return render_template(
        "reports.html",
        category_stats=category_stats,
        productive_authors=productive_authors,
        library_totals=library_totals,
    )


@app.route("/loans")
def loans():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT l.loan_id, b.title, m.name AS member_name, l.loan_date "
                "FROM LOAN l JOIN BOOK b ON b.book_id = l.book_id "
                "     JOIN MEMBER m ON m.member_id = l.member_id "
                "WHERE l.return_date IS NULL "
                "ORDER BY l.loan_date ASC;"
            )
            open_loans = cursor.fetchall()

            cursor.execute(
                "SELECT m.name, m.email, m.join_date "
                "FROM MEMBER m LEFT JOIN LOAN l ON l.member_id = m.member_id "
                "WHERE l.loan_id IS NULL ORDER BY m.name ASC;"
            )
            idle_members = cursor.fetchall()

            cursor.execute(
                "SELECT b.title, a.name AS author_name "
                "FROM BOOK b JOIN AUTHOR a ON a.author_id = b.author_id "
                "     LEFT JOIN LOAN l ON l.book_id = b.book_id "
                "WHERE l.loan_id IS NULL ORDER BY b.title ASC;"
            )
            never_borrowed = cursor.fetchall()
    finally:
        conn.close()
    return render_template(
        "loans.html",
        open_loans=open_loans,
        idle_members=idle_members,
        never_borrowed=never_borrowed,
    )


@app.route("/most_borrowed")
def most_borrowed():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT b.title, COUNT(l.loan_id) AS loan_count "
                "FROM BOOK b JOIN LOAN l ON l.book_id = b.book_id "
                "GROUP BY b.book_id, b.title "
                "ORDER BY loan_count DESC, b.title ASC LIMIT 3;"
            )
            top_books = cursor.fetchall()

            cursor.execute(
                "SELECT m.name, m.email, COUNT(l.loan_id) AS loan_count "
                "FROM MEMBER m JOIN LOAN l ON l.member_id = m.member_id "
                "GROUP BY m.member_id, m.name, m.email "
                "ORDER BY loan_count DESC, m.name ASC LIMIT 1;"
            )
            top_member = cursor.fetchone()
    finally:
        conn.close()
    return render_template("most_borrowed.html", top_books=top_books, top_member=top_member)


@app.route("/authors_books")
def authors_books():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_library_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT a.name AS author_name, a.country, COUNT(b.book_id) AS book_count "
                "FROM AUTHOR a LEFT JOIN BOOK b ON b.author_id = a.author_id "
                "GROUP BY a.author_id, a.name, a.country "
                "ORDER BY book_count DESC, a.name ASC;"
            )
            author_counts = cursor.fetchall()

            cursor.execute(
                "SELECT b.title, a.name AS author_name, a.country, p.name AS publisher_name "
                "FROM BOOK b JOIN AUTHOR a ON a.author_id = b.author_id "
                "     JOIN PUBLISHER p ON p.publisher_id = b.publisher_id "
                "WHERE a.country = p.country ORDER BY b.title ASC;"
            )
            same_country_books = cursor.fetchall()
    finally:
        conn.close()
    return render_template(
        "authors_books.html",
        author_counts=author_counts,
        same_country_books=same_country_books,
    )


if __name__ == "__main__":
    app.run(debug=True)
