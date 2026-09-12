"""Витрина спарсенных товаров.

Читает напрямую из MySQL, картинки отдаёт ссылками на velosklad.ru.
Запуск: .venv/bin/python -m web.app  ->  http://127.0.0.1:5001

Витрина не зависит от кода парсера — ей нужна только заполненная база.
"""

import math

from flask import Flask, abort, render_template, request

from web import db

app = Flask(__name__)

PER_PAGE = 24

SORTS = {
    "popular": ("b.year DESC, b.id DESC", "сначала новые"),
    "cheap": ("b.price IS NULL, b.price ASC", "сначала дешёвые"),
    "expensive": ("b.price DESC", "сначала дорогие"),
    "discount": ("b.discount_pct IS NULL, b.discount_pct DESC", "по размеру скидки"),
    "name": ("b.name ASC", "по названию"),
}

AVAILABILITY_LABELS = {
    "in_stock": ("В наличии", "ok"),
    "out_of_stock": ("Под заказ", "wait"),
    "preorder": ("Предзаказ", "wait"),
    "unknown": ("Снят с продажи", "off"),
}


def build_filters(args):
    """Собирает WHERE-часть из query-параметров."""
    where, params = [], []

    q = (args.get("q") or "").strip()
    if q:
        where.append("b.name LIKE %s")
        params.append(f"%{q}%")

    brand = args.get("brand") or ""
    if brand:
        where.append("b.brand = %s")
        params.append(brand)

    year = args.get("year") or ""
    if year.isdigit():
        where.append("b.year = %s")
        params.append(int(year))

    availability = args.get("availability") or ""
    if availability in AVAILABILITY_LABELS:
        where.append("b.availability = %s")
        params.append(availability)

    for key, op in (("price_min", ">="), ("price_max", "<=")):
        raw = (args.get(key) or "").strip()
        if raw.isdigit():
            where.append(f"b.price {op} %s")
            params.append(int(raw))

    if args.get("only_priced"):
        where.append("b.price IS NOT NULL")

    return (" WHERE " + " AND ".join(where)) if where else "", params


@app.route("/")
def index():
    args = request.args
    page = max(1, int(args.get("page") or 1))
    sort_key = args.get("sort") if args.get("sort") in SORTS else "popular"
    order_by = SORTS[sort_key][0]

    where_sql, params = build_filters(args)
    conn = db.connect()
    try:
        with db.cursor(conn) as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM bikes b{where_sql}", params)
            total = cur.fetchone()["n"]

            cur.execute(
                f"""SELECT b.id, b.name, b.brand, b.year, b.price, b.old_price,
                           b.discount_pct, b.availability, b.main_image, b.class_name
                      FROM bikes b{where_sql}
                     ORDER BY {order_by}
                     LIMIT %s OFFSET %s""",
                params + [PER_PAGE, (page - 1) * PER_PAGE],
            )
            bikes = cur.fetchall()

            cur.execute("""SELECT brand, COUNT(*) n FROM bikes
                            WHERE brand IS NOT NULL GROUP BY brand
                            ORDER BY n DESC LIMIT 40""")
            brands = cur.fetchall()

            cur.execute("""SELECT year, COUNT(*) n FROM bikes
                            WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC""")
            years = cur.fetchall()

            cur.execute("""SELECT COUNT(*) total, COUNT(price) priced,
                                  COUNT(DISTINCT brand) brands,
                                  SUM(availability='in_stock') in_stock
                             FROM bikes""")
            stats = cur.fetchone()
    finally:
        conn.close()

    return render_template(
        "index.html",
        bikes=bikes, brands=brands, years=years, stats=stats,
        total=total, page=page, pages=max(1, math.ceil(total / PER_PAGE)),
        sorts=SORTS, sort_key=sort_key, args=args,
        labels=AVAILABILITY_LABELS,
    )


@app.route("/bike/<int:bike_id>")
def bike(bike_id):
    conn = db.connect()
    try:
        with db.cursor(conn) as cur:
            cur.execute("SELECT * FROM bikes WHERE id = %s", (bike_id,))
            item = cur.fetchone()
            if not item:
                abort(404)

            cur.execute("""SELECT name, value, rank_label FROM bike_specs
                            WHERE bike_id = %s ORDER BY position""", (bike_id,))
            specs = cur.fetchall()

            cur.execute("""SELECT url, is_main FROM bike_images
                            WHERE bike_id = %s ORDER BY is_main DESC, position""", (bike_id,))
            images = cur.fetchall()

            cur.execute("SELECT size FROM bike_sizes WHERE bike_id = %s ORDER BY position",
                        (bike_id,))
            sizes = [r["size"] for r in cur.fetchall()]

            cur.execute("SELECT feature FROM bike_features WHERE bike_id = %s ORDER BY position",
                        (bike_id,))
            features = [r["feature"] for r in cur.fetchall()]

            cur.execute("""SELECT id, name, price, main_image, availability FROM bikes
                            WHERE brand = %s AND id <> %s AND price IS NOT NULL
                            ORDER BY ABS(COALESCE(price,0) - COALESCE(%s,0)) LIMIT 4""",
                        (item["brand"], bike_id, item["price"]))
            similar = cur.fetchall()
    finally:
        conn.close()

    return render_template("product.html", b=item, specs=specs, images=images,
                           sizes=sizes, features=features, similar=similar,
                           labels=AVAILABILITY_LABELS)


CATALOG_SORTS = {
    "cheap": ("price IS NULL, price ASC", "сначала дешёвые"),
    "expensive": ("price DESC", "сначала дорогие"),
    "discount": ("discount_pct IS NULL, discount_pct DESC", "по размеру скидки"),
    "name": ("name ASC", "по названию"),
}

# Запчасти и аксессуары устроены одинаково, поэтому оба раздела обслуживаются
# общими функциями: различаются только таблицы и адреса.
CATALOG_SECTIONS = {
    "parts": {
        "title": "Запчасти", "one": "запчастей",
        "main": "parts", "specs": "part_specs", "images": "part_images",
        "id_col": "part_id", "list_url": "/parts", "item_url": "/part",
    },
    "accessories": {
        "title": "Аксессуары", "one": "аксессуаров",
        "main": "accessories", "specs": "accessory_specs", "images": "accessory_images",
        "id_col": "accessory_id", "list_url": "/accessories", "item_url": "/accessory",
    },
    "equipment": {
        "title": "Экипировка", "one": "позиций",
        "main": "equipment", "specs": "equipment_specs", "images": "equipment_images",
        "id_col": "equipment_id", "list_url": "/equipment", "item_url": "/equipment-item",
    },
}


def build_catalog_filters(args):
    where, params = [], []

    q = (args.get("q") or "").strip()
    if q:
        where.append("name LIKE %s")
        params.append(f"%{q}%")

    for key, column in (("brand", "brand"), ("category", "category"),
                        ("subcategory", "subcategory")):
        value = args.get(key) or ""
        if value:
            where.append(f"{column} = %s")
            params.append(value)

    for key, op in (("price_min", ">="), ("price_max", "<=")):
        raw = (args.get(key) or "").strip()
        if raw.isdigit():
            where.append(f"price {op} %s")
            params.append(int(raw))

    return (" WHERE " + " AND ".join(where)) if where else "", params


def catalog_view(section):
    cfg = CATALOG_SECTIONS[section]
    args = request.args
    page = max(1, int(args.get("page") or 1))
    sort_key = args.get("sort") if args.get("sort") in CATALOG_SORTS else "cheap"
    order_by = CATALOG_SORTS[sort_key][0]

    where_sql, params = build_catalog_filters(args)
    conn = db.connect()
    try:
        with db.cursor(conn) as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM {cfg['main']}{where_sql}", params)
            total = cur.fetchone()["n"]

            cur.execute(
                f"""SELECT id, name, brand, category, subcategory, price, old_price,
                           discount_pct, availability, main_image
                      FROM {cfg['main']}{where_sql}
                     ORDER BY {order_by} LIMIT %s OFFSET %s""",
                params + [PER_PAGE, (page - 1) * PER_PAGE],
            )
            items = cur.fetchall()

            cur.execute(f"""SELECT category, COUNT(*) n FROM {cfg['main']}
                             WHERE category IS NOT NULL GROUP BY category
                             ORDER BY n DESC""")
            categories = cur.fetchall()

            cur.execute(f"""SELECT brand, COUNT(*) n FROM {cfg['main']}
                             WHERE brand IS NOT NULL GROUP BY brand
                             ORDER BY n DESC LIMIT 40""")
            brands = cur.fetchall()

            subcategories = []
            if args.get("category"):
                cur.execute(f"""SELECT subcategory, COUNT(*) n FROM {cfg['main']}
                                 WHERE category = %s AND subcategory IS NOT NULL
                                 GROUP BY subcategory ORDER BY n DESC""",
                            (args.get("category"),))
                subcategories = cur.fetchall()

            cur.execute(f"""SELECT COUNT(*) total, COUNT(price) priced,
                                   COUNT(DISTINCT brand) brands,
                                   COUNT(DISTINCT category) cats FROM {cfg['main']}""")
            stats = cur.fetchone()
    finally:
        conn.close()

    return render_template(
        "catalog.html", items=items, categories=categories, subcategories=subcategories,
        brands=brands, stats=stats, total=total, page=page,
        pages=max(1, math.ceil(total / PER_PAGE)),
        sorts=CATALOG_SORTS, sort_key=sort_key, args=args,
        labels=AVAILABILITY_LABELS, cfg=cfg, section=section,
    )


def item_view(section, item_id):
    cfg = CATALOG_SECTIONS[section]
    conn = db.connect()
    try:
        with db.cursor(conn) as cur:
            cur.execute(f"SELECT * FROM {cfg['main']} WHERE id = %s", (item_id,))
            item = cur.fetchone()
            if not item:
                abort(404)

            cur.execute(f"""SELECT name, value FROM {cfg['specs']}
                             WHERE {cfg['id_col']} = %s ORDER BY position""", (item_id,))
            specs = cur.fetchall()

            cur.execute(f"""SELECT url, is_main FROM {cfg['images']}
                             WHERE {cfg['id_col']} = %s
                             ORDER BY is_main DESC, position""", (item_id,))
            images = cur.fetchall()

            # Похожие: та же подкатегория, ближайшие по цене.
            cur.execute(f"""SELECT id, name, price, main_image FROM {cfg['main']}
                             WHERE subcategory <=> %s AND category <=> %s AND id <> %s
                             ORDER BY ABS(price - %s) LIMIT 4""",
                        (item["subcategory"], item["category"], item_id, item["price"]))
            similar = cur.fetchall()
    finally:
        conn.close()

    return render_template("item.html", p=item, specs=specs, images=images,
                           similar=similar, labels=AVAILABILITY_LABELS,
                           cfg=cfg, section=section)


@app.route("/parts")
def parts():
    return catalog_view("parts")


@app.route("/part/<int:item_id>")
def part(item_id):
    return item_view("parts", item_id)


@app.route("/accessories")
def accessories():
    return catalog_view("accessories")


@app.route("/accessory/<int:item_id>")
def accessory(item_id):
    return item_view("accessories", item_id)


@app.route("/equipment")
def equipment():
    return catalog_view("equipment")


@app.route("/equipment-item/<int:item_id>")
def equipment_item(item_id):
    return item_view("equipment", item_id)


@app.template_filter("money")
def money(value):
    if value is None:
        return "—"
    return f"{int(value):,}".replace(",", " ") + " ₽"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
