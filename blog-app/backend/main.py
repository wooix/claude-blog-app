import sqlite3
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(__file__), "blog.db")

app = FastAPI(title="Blog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


class PostCreate(BaseModel):
    title: str
    content: str


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: str


@app.on_event("startup")
def startup():
    init_db()


@app.get("/posts", response_model=list[PostResponse])
def list_posts():
    conn = get_db()
    rows = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return dict(row)


@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate):
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO posts (title, content, created_at) VALUES (?, ?, ?)",
        (post.title, post.content, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    conn = get_db()
    affected = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,)).rowcount
    conn.commit()
    conn.close()
    if not affected:
        raise HTTPException(status_code=404, detail="Post not found")
