from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "economic_objects.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("THREE_SECRET_KEY", "three-dev-key")
app.config["DB_PATH"] = Path(os.getenv("THREE_DB_PATH", str(DEFAULT_DB_PATH)))


@dataclass
class ColumnDef:
    name: str
    type: str


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(app.config["DB_PATH"])
    conn.row_factory = sqlite3.Row
    return conn


def initialize_demo_db() -> None:
    db_path = app.config["DB_PATH"]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            origin_country TEXT NOT NULL,
            base_price_2025 REAL NOT NULL,
            ecosystem_impact REAL NOT NULL,
            economic_impact REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_object_id INTEGER NOT NULL,
            target_object_id INTEGER NOT NULL,
            probability REAL NOT NULL DEFAULT 1,
            relation_type TEXT NOT NULL DEFAULT '=>',
            FOREIGN KEY(source_object_id) REFERENCES objects(id),
            FOREIGN KEY(target_object_id) REFERENCES objects(id)
        );
        """
    )

    objects = [
        ("Chaise bois", "Mobilier", "France", 49.90, 3.6, 2.8, 1200),
        ("Bois brut", "Ressource", "Brésil", 12.50, 4.5, 1.2, 8000),
        ("Transport maritime", "Logistique", "International", 5.90, 5.0, 2.0, 99999),
        ("Copeaux recyclés", "Matière", "France", 3.20, 1.0, 1.4, 3000),
    ]
    cursor.executemany(
        """
        INSERT INTO objects(name, category, origin_country, base_price_2025, ecosystem_impact, economic_impact, stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        objects,
    )

    links = [
        (2, 1, 0.9, "=>"),
        (3, 1, 0.8, "=>"),
        (4, 1, 0.4, "=>"),
        (2, 4, 0.7, "<=>"),
    ]
    cursor.executemany(
        """
        INSERT INTO links(source_object_id, target_object_id, probability, relation_type)
        VALUES (?, ?, ?, ?)
        """,
        links,
    )

    conn.commit()
    conn.close()


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [row[0] for row in rows]


def table_columns(conn: sqlite3.Connection, table_name: str) -> list[ColumnDef]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [ColumnDef(name=row[1], type=row[2]) for row in rows]


def fetch_table_preview(conn: sqlite3.Connection, table_name: str, limit: int = 20) -> list[sqlite3.Row]:
    return conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}").fetchall()


def detect_objects_table(conn: sqlite3.Connection) -> str | None:
    for table_name in list_tables(conn):
        columns = {col.name for col in table_columns(conn, table_name)}
        required = {"name", "base_price_2025", "origin_country"}
        if required.issubset(columns):
            return table_name
    return None


def safe_select_query(query: str) -> bool:
    q = query.strip().lower()
    forbidden = ["insert", "update", "delete", "drop", "alter", "pragma", "attach", "detach"]
    if not q.startswith("select"):
        return False
    return not any(keyword in q for keyword in forbidden)


initialize_demo_db()

@app.route("/")
def home() -> str:
    with get_connection() as conn:
        tables = list_tables(conn)
        objects_table = detect_objects_table(conn)
        avg_price = None
        if objects_table:
            avg_price = conn.execute(f"SELECT AVG(base_price_2025) AS avg_price FROM {objects_table}").fetchone()[0]

        latest_objects = []
        if objects_table:
            latest_objects = conn.execute(
                f"SELECT name, category, origin_country, base_price_2025 FROM {objects_table} ORDER BY id DESC LIMIT 5"
            ).fetchall()

    return render_template("home.html", tables=tables, avg_price=avg_price, latest_objects=latest_objects)


@app.route("/objects")
def objects_view() -> str:
    search = request.args.get("q", "").strip()
    order = request.args.get("order", "base_price_2025_desc")
    order_by = "base_price_2025 DESC"
    if order == "base_price_2025_asc":
        order_by = "base_price_2025 ASC"
    elif order == "name_asc":
        order_by = "name ASC"

    with get_connection() as conn:
        table_name = detect_objects_table(conn)
        if not table_name:
            flash("Table d'objets non trouvée. Vérifie la BDD économique.")
            return render_template("objects.html", rows=[], search=search, order=order)

        query = f"SELECT * FROM {table_name}"
        params: list[Any] = []
        if search:
            query += " WHERE name LIKE ? OR category LIKE ? OR origin_country LIKE ?"
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])
        query += f" ORDER BY {order_by} LIMIT 100"
        rows = conn.execute(query, params).fetchall()

    return render_template("objects.html", rows=rows, search=search, order=order)


@app.route("/origin")
def origin_lookup() -> str:
    name = request.args.get("name", "").strip()
    result = None
    with get_connection() as conn:
        table_name = detect_objects_table(conn)
        if table_name and name:
            result = conn.execute(
                f"SELECT name, origin_country, category FROM {table_name} WHERE name LIKE ? LIMIT 1", (f"%{name}%",)
            ).fetchone()
    return render_template("origin.html", name=name, result=result)


@app.route("/query", methods=["GET", "POST"])
def sql_query() -> str:
    query = "SELECT * FROM objects LIMIT 20"
    rows: list[sqlite3.Row] = []
    columns: list[str] = []
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if not safe_select_query(query):
            error = "Seules les requêtes SELECT non-destructives sont autorisées."
        else:
            try:
                with get_connection() as conn:
                    cursor = conn.execute(query)
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description or []]
            except sqlite3.Error as exc:
                error = str(exc)

    return render_template("query.html", query=query, rows=rows, columns=columns, error=error)


@app.route("/simulate", methods=["GET", "POST"])
def simulate() -> str:
    selected_name = None
    delta = 0.0
    result_rows: list[sqlite3.Row] = []

    with get_connection() as conn:
        table_name = detect_objects_table(conn)
        if not table_name:
            flash("Impossible de simuler sans table d'objets compatible.")
            return redirect(url_for("home"))

        objects = conn.execute(f"SELECT id, name, base_price_2025 FROM {table_name} ORDER BY name").fetchall()

        if request.method == "POST":
            object_id = request.form.get("object_id", type=int)
            delta = request.form.get("delta", type=float, default=0.0)

            if object_id is not None:
                target = conn.execute(f"SELECT id, name, base_price_2025 FROM {table_name} WHERE id = ?", (object_id,)).fetchone()
                if target:
                    selected_name = target["name"]
                    links = conn.execute(
                        """
                        SELECT l.target_object_id, l.probability, o.name, o.base_price_2025
                        FROM links l
                        JOIN objects o ON o.id = l.target_object_id
                        WHERE l.source_object_id = ?
                        """,
                        (object_id,),
                    ).fetchall()

                    result_rows.append(
                        {
                            "name": target["name"],
                            "old_price": target["base_price_2025"],
                            "new_price": round(target["base_price_2025"] + delta, 2),
                            "probability": 1.0,
                        }
                    )

                    for link in links:
                        propagated = delta * float(link["probability"])
                        result_rows.append(
                            {
                                "name": link["name"],
                                "old_price": link["base_price_2025"],
                                "new_price": round(link["base_price_2025"] + propagated, 2),
                                "probability": link["probability"],
                            }
                        )

    return render_template("simulate.html", objects=objects, selected_name=selected_name, delta=delta, results=result_rows)


@app.route("/schema")
def schema() -> str:
    with get_connection() as conn:
        tables = list_tables(conn)
        schema_data = []
        for table in tables:
            schema_data.append(
                {
                    "name": table,
                    "columns": table_columns(conn, table),
                    "preview": fetch_table_preview(conn, table),
                }
            )

    return render_template("schema.html", schema_data=schema_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
