from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = "community_board.db"

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def setup_database():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            votes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Open'
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)

    count = db.execute("SELECT COUNT(*) AS total FROM issues").fetchone()["total"]

    if count == 0:
        sample_issues = [
            ("Overflowing garbage near bus stop", "Sanitation", "Acharya Campus Gate", "Garbage has not been collected for three days.", 12, "Open"),
            ("Streetlight not working", "Infrastructure", "Sector 5 Main Road", "The road becomes unsafe and dark after 7 PM.", 8, "In Progress"),
            ("Water leakage on footpath", "Water", "Market Road", "Water is continuously leaking and making the path slippery.", 15, "Open"),
            ("Large pothole near school", "Road Safety", "Green Valley School", "A deep pothole is causing traffic and accident risk.", 21, "Open")
        ]

        db.executemany("""
            INSERT INTO issues (title, category, location, description, votes, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_issues)

    db.commit()
    db.close()

@app.route("/")
def index():
    category = request.args.get("category", "All")
    db = get_db()

    categories = db.execute(
        "SELECT DISTINCT category FROM issues ORDER BY category"
    ).fetchall()

    if category == "All":
        issues = db.execute(
            "SELECT * FROM issues ORDER BY votes DESC, id DESC"
        ).fetchall()
    else:
        issues = db.execute(
            "SELECT * FROM issues WHERE category = ? ORDER BY votes DESC, id DESC",
            (category,)
        ).fetchall()

    total_issues = db.execute(
        "SELECT COUNT(*) AS total FROM issues"
    ).fetchone()["total"]

    total_votes = db.execute(
        "SELECT COALESCE(SUM(votes), 0) AS total FROM issues"
    ).fetchone()["total"]

    resolved_issues = db.execute(
        "SELECT COUNT(*) AS total FROM issues WHERE status = 'Resolved'"
    ).fetchone()["total"]

    comments = db.execute(
        "SELECT * FROM comments ORDER BY id DESC"
    ).fetchall()

    comments_by_issue = {}
    for comment in comments:
        comments_by_issue.setdefault(comment["issue_id"], []).append(comment)

    db.close()

    return render_template(
        "index.html",
        issues=issues,
        categories=categories,
        selected_category=category,
        total_issues=total_issues,
        total_votes=total_votes,
        resolved_issues=resolved_issues,
        comments_by_issue=comments_by_issue
    )

@app.route("/add-issue", methods=["POST"])
def add_issue():
    db = get_db()
    db.execute("""
        INSERT INTO issues (title, category, location, description)
        VALUES (?, ?, ?, ?)
    """, (
        request.form["title"],
        request.form["category"],
        request.form["location"],
        request.form["description"]
    ))
    db.commit()
    db.close()
    return redirect(url_for("index"))

@app.route("/upvote/<int:issue_id>", methods=["POST"])
def upvote(issue_id):
    db = get_db()
    db.execute("UPDATE issues SET votes = votes + 1 WHERE id = ?", (issue_id,))
    db.commit()
    db.close()
    return redirect(url_for("index"))

@app.route("/add-comment/<int:issue_id>", methods=["POST"])
def add_comment(issue_id):
    db = get_db()
    db.execute("""
        INSERT INTO comments (issue_id, name, message)
        VALUES (?, ?, ?)
    """, (issue_id, request.form["name"], request.form["message"]))
    db.commit()
    db.close()
    return redirect(url_for("index"))

@app.route("/change-status/<int:issue_id>", methods=["POST"])
def change_status(issue_id):
    db = get_db()
    db.execute(
        "UPDATE issues SET status = ? WHERE id = ?",
        (request.form["status"], issue_id)
    )
    db.commit()
    db.close()
    return redirect(url_for("index"))

@app.route("/delete-issue/<int:issue_id>", methods=["POST"])
def delete_issue(issue_id):
    db = get_db()
    db.execute("DELETE FROM comments WHERE issue_id = ?", (issue_id,))
    db.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
    db.commit()
    db.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    setup_database()
    app.run(debug=True)
