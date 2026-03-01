from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import date

app = Flask(__name__)

DB = "planner.db"

# ======================
# DATABASE INIT
# ======================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        time TEXT,
        category TEXT,
        completed INTEGER DEFAULT 0,
        last_reset TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ======================
# HOME PAGE
# ======================
@app.route("/")
def home():
    return render_template("index.html")


# ======================
# REGISTER
# ======================
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data["name"]
    email = data["email"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()

    if user:
        conn.close()
        return jsonify({"message": "User already exists"})

    c.execute("INSERT INTO users(name,email) VALUES (?,?)", (name,email))
    conn.commit()

    user_id = c.lastrowid
    conn.close()

    return jsonify({
        "message":"Registered successfully!",
        "userId":user_id
    })


# ======================
# LOGIN
# ======================
@app.route("/login", methods=["POST"])
def login():

    data = request.json
    email = data["email"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT id,name FROM users WHERE email=?", (email,))
    user = c.fetchone()

    conn.close()

    if not user:
        return jsonify({"message":"User not found"})

    return jsonify({
        "message":"Login successful!",
        "userId":user[0],
        "name":user[1]
    })


# ======================
# ADD TASK
# ======================
@app.route("/add-task", methods=["POST"])
def add_task():

    data = request.json
    today = str(date.today())

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO tasks(user_id,title,time,category,last_reset)
    VALUES (?,?,?,?,?)
    """,(data["userId"],data["title"],data["time"],
         data["category"],today))

    conn.commit()
    conn.close()

    return jsonify({"message":"Task added!"})


# ======================
# GET TASKS
# ======================
@app.route("/tasks/<int:user_id>")
def get_tasks(user_id):

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT id,title,time,category,completed
    FROM tasks WHERE user_id=?
    """,(user_id,))

    rows = c.fetchall()
    conn.close()

    tasks=[]
    for r in rows:
        tasks.append({
            "_id":r[0],
            "title":r[1],
            "time":r[2],
            "category":r[3],
            "completed":bool(r[4])
        })

    return jsonify(tasks)


# ======================
# TOGGLE TASK
# ======================
@app.route("/task/<int:task_id>", methods=["PUT"])
def toggle_task(task_id):

    data = request.json
    val = 1 if data["completed"] else 0

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("UPDATE tasks SET completed=? WHERE id=?",
              (val,task_id))

    conn.commit()
    conn.close()

    return jsonify({"message":"Updated"})


# ======================
# DAILY RESET
# ======================
@app.route("/daily-reset/<int:user_id>", methods=["POST"])
def daily_reset(user_id):

    today = str(date.today())

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    UPDATE tasks
    SET completed=0,last_reset=?
    WHERE user_id=? AND last_reset != ?
    """,(today,user_id,today))

    conn.commit()
    conn.close()

    return jsonify({"message":"Reset checked"})


if __name__ == "__main__":
    app.run()
