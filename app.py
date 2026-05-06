import os
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("DB_PATH", BASE_DIR / "campus_trade.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")


INITIAL_USERS = [
    ("u001", "ZhangSan", "13800000001"),
    ("u002", "LiSi", "13800000002"),
    ("u003", "WangWu", "13800000003"),
    ("u004", "ZhaoLiu", "13800000004"),
]

INITIAL_ITEMS = [
    ("i001", "CalculusBook", "Book", 20, 0, "u001"),
    ("i002", "DeskLamp", "DailyGoods", 35, 1, "u002"),
    ("i003", "Microcontroller", "Electronics", 80, 0, "u001"),
    ("i004", "Chair", "Furniture", 50, 1, "u003"),
    ("i005", "WaterBottle", "DailyGoods", 15, 0, "u004"),
]

INITIAL_ORDERS = [
    ("o001", "i002", "u001", "2024-05-01"),
    ("o002", "i004", "u002", "2024-05-03"),
]


QUERY_DEFINITIONS = {
    "unsold": {
        "section": "基本查询",
        "label": "未售商品",
        "title": "查询所有未售出的商品",
        "description": "按 status = 0 查询未售商品，可选卖家筛选。",
        "inputs": [
            {"name": "seller_id", "label": "卖家 ID", "type": "text", "default": ""},
        ],
    },
    "price_filter": {
        "section": "基本查询",
        "label": "价格条件",
        "title": "查询价格大于指定值的商品",
        "description": "默认阈值为 30，也可以改成任意价格。",
        "inputs": [
            {
                "name": "min_price",
                "label": "最低价格",
                "type": "number",
                "step": "0.01",
                "default": "30",
            }
        ],
    },
    "category_items": {
        "section": "基本查询",
        "label": "分类查询",
        "title": "查询指定分类的商品",
        "description": "默认分类为 DailyGoods，也支持输入任意分类。",
        "inputs": [
            {"name": "category", "label": "分类", "type": "text", "default": "DailyGoods"},
        ],
    },
    "seller_items": {
        "section": "基本查询",
        "label": "卖家发布商品",
        "title": "查询某个卖家发布的所有商品",
        "description": "默认 seller_id 为 u001，也可以改成 u002 等其他用户。",
        "inputs": [
            {"name": "seller_id", "label": "卖家 ID", "type": "text", "default": "u001"},
        ],
    },
    "sold_with_buyer": {
        "section": "连接查询",
        "label": "已售商品与买家",
        "title": "查询所有已售商品及其买家姓名",
        "description": "可选按买家或卖家筛选已售商品结果。",
        "inputs": [
            {"name": "buyer_id", "label": "买家 ID", "type": "text", "default": ""},
            {"name": "seller_id", "label": "卖家 ID", "type": "text", "default": ""},
        ],
    },
    "order_details": {
        "section": "连接查询",
        "label": "每个订单",
        "title": "查询每个订单：商品名、买家名和日期",
        "description": "展示订单对应的商品名、买家姓名和具体订单日期，可按商品名、买家姓名或订单日期筛选。",
        "inputs": [
            {"name": "item_name", "label": "商品名", "type": "text", "default": ""},
            {"name": "buyer_id", "label": "买家名或ID", "type": "text", "default": ""},
            {"name": "order_date", "label": "订单日期", "type": "date", "default": ""},
        ],
    },
    "seller_purchase_status": {
        "section": "连接查询",
        "label": "卖家商品是否被购买",
        "title": "查询某个卖家的商品是否被购买",
        "description": "默认查看 u001，也支持改成任意卖家。",
        "inputs": [
            {"name": "seller_id", "label": "卖家 ID", "type": "text", "default": "u001"},
        ],
    },
    "total_items": {
        "section": "聚合与分组",
        "label": "商品总数",
        "title": "统计商品总数",
        "description": "可选按分类统计该分类下的商品总数。",
        "inputs": [
            {"name": "category", "label": "分类", "type": "text", "default": ""},
        ],
    },
    "category_counts": {
        "section": "聚合与分组",
        "label": "每类商品数量",
        "title": "统计每类商品数量",
        "description": "可选按状态过滤后再分组统计。",
        "inputs": [
            {
                "name": "status",
                "label": "商品状态",
                "type": "select",
                "default": "",
                "options": [
                    {"value": "", "label": "全部"},
                    {"value": "0", "label": "未售出"},
                    {"value": "1", "label": "已售出"},
                ],
            }
        ],
    },
    "avg_price": {
        "section": "聚合与分组",
        "label": "平均价格",
        "title": "计算商品平均价格",
        "description": "可选按分类求平均价格。",
        "inputs": [
            {"name": "category", "label": "分类", "type": "text", "default": ""},
        ],
    },
    "top_seller": {
        "section": "聚合与分组",
        "label": "发布最多的用户",
        "title": "查询发布商品数量最多的用户",
        "description": "可选按分类比较谁发布得最多。",
        "inputs": [
            {"name": "category", "label": "分类", "type": "text", "default": ""},
        ],
    },
    "sold_view": {
        "section": "视图",
        "label": "已售商品视图",
        "title": "查看已售商品视图 sold_item_view",
        "description": "可选按买家 ID 查看视图中的结果。",
        "inputs": [
            {"name": "buyer_id", "label": "买家 ID", "type": "text", "default": ""},
        ],
    },
    "unsold_view": {
        "section": "视图",
        "label": "未售商品视图",
        "title": "查看未售商品视图 unsold_item_view",
        "description": "可选按卖家 ID 查看未售商品视图。",
        "inputs": [
            {"name": "seller_id", "label": "卖家 ID", "type": "text", "default": ""},
        ],
    },
}


QUERY_SECTIONS = ["基本查询", "连接查询", "聚合与分组", "视图"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def create_schema(db):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS user (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS item (
            item_id TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL CHECK (price >= 0),
            status INTEGER NOT NULL CHECK (status IN (0, 1)),
            seller_id TEXT NOT NULL,
            FOREIGN KEY (seller_id) REFERENCES user(user_id)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL UNIQUE,
            buyer_id TEXT NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES item(item_id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (buyer_id) REFERENCES user(user_id)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );

        CREATE TRIGGER IF NOT EXISTS orders_item_must_be_sold_insert
        BEFORE INSERT ON orders
        FOR EACH ROW
        WHEN (SELECT status FROM item WHERE item_id = NEW.item_id) != 1
        BEGIN
            SELECT RAISE(ABORT, 'ordered item status must be 1');
        END;

        CREATE TRIGGER IF NOT EXISTS orders_item_must_be_sold_update
        BEFORE UPDATE OF item_id ON orders
        FOR EACH ROW
        WHEN (SELECT status FROM item WHERE item_id = NEW.item_id) != 1
        BEGIN
            SELECT RAISE(ABORT, 'ordered item status must be 1');
        END;

        CREATE TRIGGER IF NOT EXISTS item_with_order_cannot_be_unsold
        BEFORE UPDATE OF status ON item
        FOR EACH ROW
        WHEN NEW.status = 0
             AND EXISTS (SELECT 1 FROM orders WHERE item_id = NEW.item_id)
        BEGIN
            SELECT RAISE(ABORT, 'item with order cannot be unsold');
        END;

        CREATE VIEW IF NOT EXISTS sold_item_view AS
        SELECT item.item_name, orders.buyer_id
        FROM item
        JOIN orders ON orders.item_id = item.item_id
        WHERE item.status = 1;

        CREATE VIEW IF NOT EXISTS unsold_item_view AS
        SELECT item_id, item_name, category, price, seller_id
        FROM item
        WHERE status = 0;
        """
    )


def seed_data(db):
    db.executemany(
        "INSERT INTO user (user_id, user_name, phone) VALUES (?, ?, ?)",
        INITIAL_USERS,
    )
    db.executemany(
        """
        INSERT INTO item (item_id, item_name, category, price, status, seller_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        INITIAL_ITEMS,
    )
    db.executemany(
        """
        INSERT INTO orders (order_id, item_id, buyer_id, order_date)
        VALUES (?, ?, ?, ?)
        """,
        INITIAL_ORDERS,
    )


def reset_schema(db):
    db.executescript(
        """
        DROP VIEW IF EXISTS sold_item_view;
        DROP VIEW IF EXISTS unsold_item_view;
        DROP TRIGGER IF EXISTS orders_item_must_be_sold_insert;
        DROP TRIGGER IF EXISTS orders_item_must_be_sold_update;
        DROP TRIGGER IF EXISTS item_with_order_cannot_be_unsold;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS item;
        DROP TABLE IF EXISTS user;
        """
    )


def init_db(force=False):
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    try:
        if force:
            reset_schema(db)

        create_schema(db)
        user_count = db.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        if user_count == 0:
            seed_data(db)
        db.commit()
    finally:
        db.close()


@app.before_request
def ensure_database():
    if not DATABASE.exists():
        init_db()


def rows(sql, params=()):
    return get_db().execute(sql, params).fetchall()


def one(sql, params=()):
    return get_db().execute(sql, params).fetchone()


def next_id(prefix, table_name, column_name):
    value = one(
        f"SELECT {column_name} FROM {table_name} "
        f"WHERE {column_name} LIKE ? ORDER BY {column_name} DESC LIMIT 1",
        (f"{prefix}%",),
    )
    number = int(value[column_name][1:]) + 1 if value else 1
    return f"{prefix}{number:03d}"


def build_query_sections():
    grouped = []
    for section_name in QUERY_SECTIONS:
        entries = []
        for key, config in QUERY_DEFINITIONS.items():
            if config["section"] == section_name:
                entries.append({"key": key, **config})
        grouped.append({"name": section_name, "queries": entries})
    return grouped


def get_query_values(query_key):
    config = QUERY_DEFINITIONS[query_key]
    values = {}
    for field in config["inputs"]:
        values[field["name"]] = request.args.get(field["name"], field.get("default", "")).strip()
    return values


def build_query_result(query_key, values):
    if query_key == "unsold":
        sql = "SELECT * FROM unsold_item_view"
        params = []
        if values["seller_id"]:
            sql += " WHERE seller_id = ?"
            params.append(values["seller_id"])
        sql += " ORDER BY item_id"
        return sql, params, rows(sql, tuple(params))

    if query_key == "price_filter":
        min_price = float(values["min_price"] or 30)
        sql = "SELECT * FROM item WHERE price > ? ORDER BY price DESC, item_id"
        params = [min_price]
        return sql, params, rows(sql, tuple(params))

    if query_key == "category_items":
        sql = "SELECT * FROM item WHERE category = ? ORDER BY item_id"
        params = [values["category"] or "DailyGoods"]
        return sql, params, rows(sql, tuple(params))

    if query_key == "seller_items":
        sql = "SELECT * FROM item WHERE seller_id = ? ORDER BY item_id"
        params = [values["seller_id"] or "u001"]
        return sql, params, rows(sql, tuple(params))

    if query_key == "sold_with_buyer":
        sql = """
            SELECT item.item_id, item.item_name, item.price, item.seller_id,
                   orders.buyer_id, user.user_name AS buyer_name
            FROM item
            JOIN orders ON orders.item_id = item.item_id
            JOIN user ON user.user_id = orders.buyer_id
            WHERE item.status = 1
        """
        params = []
        if values["buyer_id"]:
            sql += " AND orders.buyer_id = ?"
            params.append(values["buyer_id"])
        if values["seller_id"]:
            sql += " AND item.seller_id = ?"
            params.append(values["seller_id"])
        sql += " ORDER BY item.item_id"
        return sql, params, rows(sql, tuple(params))

    if query_key == "order_details":
        sql = """
            SELECT orders.order_id AS "订单编号",
                   item.item_name AS "商品名",
                   orders.buyer_id AS "买家ID",
                   user.user_name AS "买家名",
                   orders.order_date AS "日期"
            FROM orders
            JOIN item ON item.item_id = orders.item_id
            JOIN user ON user.user_id = orders.buyer_id
            WHERE 1 = 1
        """
        params = []
        if values["item_name"]:
            sql += " AND item.item_name LIKE ?"
            params.append(f"%{values['item_name']}%")
        if values["buyer_id"]:
            sql += " AND (orders.buyer_id = ? OR user.user_name LIKE ?)"
            params.extend([values["buyer_id"], f"%{values['buyer_id']}%"])
        if values["order_date"]:
            sql += " AND orders.order_date = ?"
            params.append(values["order_date"].replace("/", "-"))
        sql += " ORDER BY orders.order_id"
        return sql, params, rows(sql, tuple(params))

    if query_key == "seller_purchase_status":
        sql = """
            SELECT item.item_id, item.item_name,
                   CASE WHEN orders.order_id IS NULL THEN '未购买' ELSE '已购买' END
                   AS purchase_status,
                   orders.order_id
            FROM item
            LEFT JOIN orders ON orders.item_id = item.item_id
            WHERE item.seller_id = ?
            ORDER BY item.item_id
        """
        params = [values["seller_id"] or "u001"]
        return sql, params, rows(sql, tuple(params))

    if query_key == "total_items":
        sql = "SELECT COUNT(*) AS total_items FROM item"
        params = []
        if values["category"]:
            sql += " WHERE category = ?"
            params.append(values["category"])
        return sql, params, rows(sql, tuple(params))

    if query_key == "category_counts":
        sql = "SELECT category, COUNT(*) AS item_count FROM item"
        params = []
        if values["status"] in {"0", "1"}:
            sql += " WHERE status = ?"
            params.append(values["status"])
        sql += " GROUP BY category ORDER BY item_count DESC, category"
        return sql, params, rows(sql, tuple(params))

    if query_key == "avg_price":
        sql = "SELECT ROUND(AVG(price), 2) AS avg_price FROM item"
        params = []
        if values["category"]:
            sql += " WHERE category = ?"
            params.append(values["category"])
        return sql, params, rows(sql, tuple(params))

    if query_key == "top_seller":
        sql = """
            SELECT user.user_id, user.user_name, COUNT(item.item_id) AS item_count
            FROM user
            JOIN item ON item.seller_id = user.user_id
        """
        params = []
        if values["category"]:
            sql += " WHERE item.category = ?"
            params.append(values["category"])
        sql += """
            GROUP BY user.user_id, user.user_name
            ORDER BY item_count DESC, user.user_id
            LIMIT 1
        """
        return sql, params, rows(sql, tuple(params))

    if query_key == "sold_view":
        sql = "SELECT * FROM sold_item_view"
        params = []
        if values["buyer_id"]:
            sql += " WHERE buyer_id = ?"
            params.append(values["buyer_id"])
        sql += " ORDER BY item_name"
        return sql, params, rows(sql, tuple(params))

    if query_key == "unsold_view":
        sql = "SELECT * FROM unsold_item_view"
        params = []
        if values["seller_id"]:
            sql += " WHERE seller_id = ?"
            params.append(values["seller_id"])
        sql += " ORDER BY item_id"
        return sql, params, rows(sql, tuple(params))

    raise ValueError(f"Unsupported query key: {query_key}")


def get_query_page_context(query_key=None):
    summary = {
        "total_items": one("SELECT COUNT(*) AS value FROM item")["value"],
        "avg_price": one("SELECT AVG(price) AS value FROM item")["value"],
        "sold_count": one("SELECT COUNT(*) AS value FROM item WHERE status = 1")["value"],
        "category_count": one("SELECT COUNT(DISTINCT category) AS value FROM item")["value"],
    }

    query_key = query_key or request.args.get("query", "seller_items")
    if query_key not in QUERY_DEFINITIONS:
        query_key = "seller_items"

    active_query = QUERY_DEFINITIONS[query_key]
    values = get_query_values(query_key)
    sql_text, sql_params, result_rows = build_query_result(query_key, values)

    return {
        "active_key": query_key,
        "active_query": active_query,
        "values": values,
        "sql_text": sql_text.strip(),
        "sql_params": sql_params,
        "result_rows": result_rows,
        "query_sections": build_query_sections(),
        "summary": summary,
    }


@app.route("/")
def index():
    stats = {
        "user_count": one("SELECT COUNT(*) AS value FROM user")["value"],
        "item_count": one("SELECT COUNT(*) AS value FROM item")["value"],
        "order_count": one("SELECT COUNT(*) AS value FROM orders")["value"],
        "unsold_count": one("SELECT COUNT(*) AS value FROM item WHERE status = 0")["value"],
    }
    return render_template("index.html", stats=stats)


@app.route("/users")
def users():
    return render_template("users.html", users=rows("SELECT * FROM user ORDER BY user_id"))


@app.route("/items")
def items():
    return render_template(
        "items.html",
        items=rows(
            """
            SELECT item.*, user.user_name AS seller_name
            FROM item
            JOIN user ON user.user_id = item.seller_id
            ORDER BY item.item_id
            """
        ),
        users=rows("SELECT user_id, user_name FROM user ORDER BY user_id"),
    )


@app.route("/orders")
def orders_page():
    return render_template(
        "orders.html",
        orders=rows(
            """
            SELECT orders.*, item.item_name, user.user_name AS buyer_name
            FROM orders
            JOIN item ON item.item_id = orders.item_id
            JOIN user ON user.user_id = orders.buyer_id
            ORDER BY orders.order_id
            """
        ),
    )


@app.route("/notes")
def notes():
    return render_template("notes.html")


@app.post("/items/add")
def add_item():
    item_id = request.form.get("item_id", "").strip() or next_id("i", "item", "item_id")
    try:
        get_db().execute(
            """
            INSERT INTO item (item_id, item_name, category, price, status, seller_id)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                item_id,
                request.form["item_name"].strip(),
                request.form["category"].strip(),
                float(request.form["price"]),
                request.form["seller_id"],
            ),
        )
        get_db().commit()
        flash("新商品已插入数据库。", "success")
    except (sqlite3.Error, ValueError) as exc:
        get_db().rollback()
        flash(f"插入失败：{exc}", "error")
    return redirect(url_for("items"))


@app.post("/items/<item_id>/price")
def update_price(item_id):
    try:
        get_db().execute(
            "UPDATE item SET price = ? WHERE item_id = ?",
            (float(request.form["price"]), item_id),
        )
        get_db().commit()
        flash(f"{item_id} 的价格已修改。", "success")
    except (sqlite3.Error, ValueError) as exc:
        get_db().rollback()
        flash(f"修改失败：{exc}", "error")
    return redirect(url_for("items"))


@app.post("/items/<item_id>/delete")
def delete_item(item_id):
    item = one("SELECT status FROM item WHERE item_id = ?", (item_id,))
    if item is None:
        flash("商品不存在。", "error")
    elif item["status"] == 1:
        flash("已售商品不能删除，只允许删除未售出商品。", "error")
    else:
        get_db().execute("DELETE FROM item WHERE item_id = ?", (item_id,))
        get_db().commit()
        flash(f"{item_id} 已从数据库删除。", "success")
    return redirect(url_for("items"))


@app.post("/purchase")
def purchase():
    item_id = request.form["item_id"]
    buyer_id = request.form["buyer_id"]
    order_date = request.form.get("order_date") or date.today().isoformat()
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        item = db.execute(
            "SELECT item_id, status, seller_id FROM item WHERE item_id = ?",
            (item_id,),
        ).fetchone()
        if item is None:
            raise ValueError("商品不存在")
        if item["status"] == 1:
            raise ValueError("已售商品不能再次购买")
        if item["seller_id"] == buyer_id:
            raise ValueError("不能购买自己发布的商品")

        db.execute("UPDATE item SET status = 1 WHERE item_id = ?", (item_id,))
        db.execute(
            """
            INSERT INTO orders (order_id, item_id, buyer_id, order_date)
            VALUES (?, ?, ?, ?)
            """,
            (next_id("o", "orders", "order_id"), item_id, buyer_id, order_date),
        )
        db.commit()
        flash("购买成功：订单已新增，商品状态已改为已售出。", "success")
    except (sqlite3.Error, ValueError) as exc:
        db.rollback()
        flash(f"购买失败：{exc}", "error")
    return redirect(url_for("items"))


@app.route("/queries")
def queries():
    return render_template("queries.html", **get_query_page_context())


@app.route("/queries/panel")
def queries_panel():
    return render_template("query_panel.html", **get_query_page_context())


@app.post("/reset")
def reset():
    close_db()
    init_db(force=True)
    flash("数据已重置为初始状态。", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
