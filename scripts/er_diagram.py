"""Рисует ER-схему базы velostok в PNG.

Запуск: .venv/bin/python scripts/er_diagram.py [выходной_файл]
"""

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

BG = "#f7f8fa"
HEAD_MAIN = "#2f4858"
HEAD_CHILD = "#4a7a8c"
HEAD_SERVICE = "#8c6a4a"
HEAD_PARTS = "#4a5c3a"
HEAD_PARTS_CHILD = "#6d8456"
HEAD_ACC = "#5a4763"
HEAD_ACC_CHILD = "#7d6a87"
BODY = "#ffffff"
BORDER = "#c9d2d9"
TEXT_HEAD = "#ffffff"
TEXT = "#25303a"
MUTED = "#7a8894"
LINE = "#8fa3b0"

ROW_H = 0.62
HEAD_H = 0.95
PAD = 0.35

TABLES = {
    "crawl_queue": {
        "pos": (0.5, 10.4),
        "width": 5.6,
        "head": HEAD_SERVICE,
        "note": "состояние обхода",
        "cols": [
            ("bike_id", "BIGINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("slug", "VARCHAR(255)", ""),
            ("status", "ENUM(5)", "idx"),
            ("attempts", "TINYINT", ""),
            ("http_status", "SMALLINT", ""),
            ("error", "TEXT", ""),
            ("fetched_at", "DATETIME", ""),
            ("updated_at", "DATETIME", ""),
        ],
    },
    "bikes": {
        "pos": (7.6, 16.1),
        "width": 6.4,
        "head": HEAD_MAIN,
        "note": "карточка товара",
        "cols": [
            ("id", "BIGINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("slug", "VARCHAR(255)", ""),
            ("name", "VARCHAR(512)", ""),
            ("brand", "VARCHAR(128)", "idx"),
            ("model", "VARCHAR(255)", ""),
            ("year", "SMALLINT", "idx"),
            ("sku", "VARCHAR(64)", ""),
            ("price", "DECIMAL(10,2)", "idx"),
            ("old_price", "DECIMAL(10,2)", ""),
            ("discount_pct", "TINYINT", ""),
            ("currency", "CHAR(3)", ""),
            ("availability", "ENUM(4)", "idx"),
            ("description", "TEXT", ""),
            ("class_name", "VARCHAR(128)", ""),
            ("class_rank", "TINYINT", ""),
            ("class_max", "TINYINT", ""),
            ("gender", "VARCHAR(128)", ""),
            ("main_image", "VARCHAR(512)", ""),
            ("parsed_at", "DATETIME", ""),
            ("created_at", "DATETIME", ""),
            ("updated_at", "DATETIME", ""),
        ],
    },
    "bike_specs": {
        "pos": (16.8, 16.1),
        "width": 5.9,
        "head": HEAD_CHILD,
        "note": "характеристики (EAV)",
        "cols": [
            ("bike_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("name", "VARCHAR(128)", "idx"),
            ("value", "TEXT", ""),
            ("rank_label", "VARCHAR(128)", ""),
        ],
    },
    "bike_images": {
        "pos": (16.8, 11.9),
        "width": 5.9,
        "head": HEAD_CHILD,
        "note": "фото (только URL)",
        "cols": [
            ("bike_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("is_main", "BOOLEAN", ""),
        ],
    },
    "bike_sizes": {
        "pos": (16.8, 8.3),
        "width": 5.9,
        "head": HEAD_CHILD,
        "note": "ростовки в наличии",
        "cols": [
            ("bike_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("size", "VARCHAR(64)", ""),
        ],
    },
    "bike_features": {
        "pos": (16.8, 5.0),
        "width": 5.9,
        "head": HEAD_CHILD,
        "note": "особенности",
        "cols": [
            ("bike_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("feature", "VARCHAR(255)", ""),
        ],
    },
    "parts_queue": {
        "pos": (32.9, 8.1),
        "width": 5.6,
        "head": HEAD_SERVICE,
        "note": "состояние обхода",
        "cols": [
            ("part_id", "BIGINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("status", "ENUM(5)", "idx"),
            ("attempts", "TINYINT", ""),
            ("http_status", "SMALLINT", ""),
            ("error", "TEXT", ""),
            ("fetched_at", "DATETIME", ""),
            ("updated_at", "DATETIME", ""),
        ],
    },
    "parts": {
        "pos": (24.8, 16.1),
        "width": 6.2,
        "head": HEAD_PARTS,
        "note": "запчасть",
        "cols": [
            ("id", "BIGINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("name", "VARCHAR(512)", ""),
            ("brand", "VARCHAR(128)", "idx"),
            ("model", "VARCHAR(255)", ""),
            ("sku", "VARCHAR(64)", ""),
            ("category", "VARCHAR(128)", "idx"),
            ("subcategory", "VARCHAR(128)", "idx"),
            ("price", "DECIMAL(10,2)", "idx"),
            ("old_price", "DECIMAL(10,2)", ""),
            ("discount_pct", "TINYINT", ""),
            ("currency", "CHAR(3)", ""),
            ("availability", "ENUM(4)", "idx"),
            ("description", "TEXT", ""),
            ("main_image", "VARCHAR(512)", ""),
            ("parsed_at", "DATETIME", ""),
        ],
    },
    "part_specs": {
        "pos": (32.9, 16.1),
        "width": 5.9,
        "head": HEAD_PARTS_CHILD,
        "note": "характеристики (EAV)",
        "cols": [
            ("part_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("name", "VARCHAR(128)", "idx"),
            ("value", "TEXT", ""),
        ],
    },
    "part_images": {
        "pos": (32.9, 12.1),
        "width": 5.9,
        "head": HEAD_PARTS_CHILD,
        "note": "фото (только URL)",
        "cols": [
            ("part_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("is_main", "BOOLEAN", ""),
        ],
    },
    "accessories_queue": {
        "pos": (49.0, 8.1),
        "width": 7.2,
        "head": HEAD_SERVICE,
        "note": "состояние обхода",
        "cols": [
            ("accessory_id", "BIGINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("status", "ENUM(5)", "idx"),
            ("attempts", "TINYINT", ""),
            ("http_status", "SMALLINT", ""),
            ("error", "TEXT", ""),
            ("fetched_at", "DATETIME", ""),
            ("updated_at", "DATETIME", ""),
        ],
    },
    "accessories": {
        "pos": (40.9, 16.1),
        "width": 6.2,
        "head": HEAD_ACC,
        "note": "аксессуар",
        "cols": [
            ("id", "BIGINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("name", "VARCHAR(512)", ""),
            ("brand", "VARCHAR(128)", "idx"),
            ("model", "VARCHAR(255)", ""),
            ("sku", "VARCHAR(64)", ""),
            ("category", "VARCHAR(128)", "idx"),
            ("subcategory", "VARCHAR(128)", "idx"),
            ("price", "DECIMAL(10,2)", "idx"),
            ("old_price", "DECIMAL(10,2)", ""),
            ("discount_pct", "TINYINT", ""),
            ("currency", "CHAR(3)", ""),
            ("availability", "ENUM(4)", "idx"),
            ("description", "TEXT", ""),
            ("main_image", "VARCHAR(512)", ""),
            ("parsed_at", "DATETIME", ""),
        ],
    },
    "accessory_specs": {
        "pos": (49.0, 16.1),
        "width": 7.2,
        "head": HEAD_ACC_CHILD,
        "note": "характеристики (EAV)",
        "cols": [
            ("accessory_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("name", "VARCHAR(128)", "idx"),
            ("value", "TEXT", ""),
        ],
    },
    "accessory_images": {
        "pos": (49.0, 12.1),
        "width": 7.2,
        "head": HEAD_ACC_CHILD,
        "note": "фото (только URL)",
        "cols": [
            ("accessory_id", "BIGINT", "PK,FK"),
            ("position", "SMALLINT", "PK"),
            ("url", "VARCHAR(512)", ""),
            ("is_main", "BOOLEAN", ""),
        ],
    },
}

# (дочерняя, родительская, подпись)
RELATIONS = [
    ("bike_specs", "bikes", "1 : N"),
    ("bike_images", "bikes", "1 : N"),
    ("bike_sizes", "bikes", "1 : N"),
    ("bike_features", "bikes", "1 : N"),
]

PARTS_RELATIONS = [
    ("part_specs", "parts", "1 : N"),
    ("part_images", "parts", "1 : N"),
]

ACC_RELATIONS = [
    ("accessory_specs", "accessories", "1 : N"),
    ("accessory_images", "accessories", "1 : N"),
]


def table_height(spec):
    return HEAD_H + len(spec["cols"]) * ROW_H + PAD


def draw_table(ax, name, spec):
    x, top = spec["pos"]
    w = spec["width"]
    h = table_height(spec)
    y = top - h

    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.18",
        facecolor=BODY, edgecolor=BORDER, linewidth=1.4, zorder=2))

    ax.add_patch(FancyBboxPatch(
        (x, top - HEAD_H), w, HEAD_H,
        boxstyle="round,pad=0,rounding_size=0.18",
        facecolor=spec["head"], edgecolor=spec["head"], linewidth=1.4, zorder=3))
    # прямоугольная нижняя кромка шапки
    ax.add_patch(plt.Rectangle((x, top - HEAD_H), w, HEAD_H * 0.45,
                               facecolor=spec["head"], edgecolor="none", zorder=3))

    ax.text(x + 0.3, top - HEAD_H * 0.42, name,
            color=TEXT_HEAD, fontsize=12.5, fontweight="bold",
            va="center", ha="left", zorder=4, family="DejaVu Sans")
    ax.text(x + w - 0.3, top - HEAD_H * 0.42, spec["note"],
            color="#dbe6ec", fontsize=8.4, va="center", ha="right",
            zorder=4, style="italic", family="DejaVu Sans")

    for i, (col, typ, key) in enumerate(spec["cols"]):
        cy = top - HEAD_H - ROW_H * (i + 0.5)
        if i % 2 == 1:
            ax.add_patch(plt.Rectangle((x + 0.08, cy - ROW_H / 2), w - 0.16, ROW_H,
                                       facecolor="#f4f7f9", edgecolor="none", zorder=3))
        bold = "PK" in key or "FK" in key
        ax.text(x + 0.32, cy, col, fontsize=9.6, va="center", ha="left",
                color=TEXT, zorder=4, family="DejaVu Sans Mono",
                fontweight="bold" if bold else "normal")
        ax.text(x + w - 1.35, cy, typ, fontsize=8.5, va="center", ha="right",
                color=MUTED, zorder=4, family="DejaVu Sans Mono")
        if key:
            color = "#b5651d" if "FK" in key else ("#2f7a4f" if "PK" in key else MUTED)
            ax.text(x + w - 0.28, cy, key, fontsize=7.8, va="center", ha="right",
                    color=color, zorder=4, fontweight="bold", family="DejaVu Sans")

    return x, y, w, h


def main(out="db_schema.png"):
    fig, ax = plt.subplots(figsize=(38.5, 12.6), dpi=170)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 56.9)
    ax.set_ylim(-0.5, 18.7)
    ax.axis("off")

    boxes = {name: draw_table(ax, name, spec) for name, spec in TABLES.items()}

    # связи «дочерняя -> bikes.id»
    px, py, pw, ph = boxes["bikes"]
    parent_anchor_x = px + pw
    for idx, (child, _parent, label) in enumerate(RELATIONS):
        cx, cy, cw, ch = boxes[child]
        child_y = cy + ch - HEAD_H - ROW_H * 0.5      # строка bike_id
        parent_y = py + ph - HEAD_H - ROW_H * 0.5     # строка id

        # своя вертикаль для каждой связи, иначе линии сливаются в одну
        corridor = cx - 0.35 - 0.42 * idx
        ax.plot([cx, corridor], [child_y, child_y],
                color=LINE, linewidth=1.5, zorder=1, solid_capstyle="round")
        ax.plot([corridor, corridor], [child_y, parent_y],
                color=LINE, linewidth=1.5, zorder=1, solid_capstyle="round")
        ax.annotate("", xy=(parent_anchor_x, parent_y), xytext=(corridor, parent_y),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.32,head_length=0.6",
                                    color=LINE, linewidth=1.5, shrinkA=0, shrinkB=2),
                    zorder=1)
        ax.text(corridor, child_y + 0.24, label,
                fontsize=8.6, color=MUTED, ha="center", va="bottom",
                zorder=5, family="DejaVu Sans",
                bbox=dict(boxstyle="round,pad=0.18", facecolor=BG, edgecolor="none"))

    # связи «дочерняя -> parts.id»
    ppx, ppy, ppw, pph = boxes["parts"]
    parts_anchor_x = ppx + ppw
    for idx, (child, _parent, label) in enumerate(PARTS_RELATIONS):
        cx, cy, cw, ch = boxes[child]
        child_y = cy + ch - HEAD_H - ROW_H * 0.5
        parent_y = ppy + pph - HEAD_H - ROW_H * 0.5
        corridor = cx - 0.35 - 0.42 * idx
        ax.plot([cx, corridor], [child_y, child_y],
                color=LINE, linewidth=1.5, zorder=1, solid_capstyle="round")
        ax.plot([corridor, corridor], [child_y, parent_y],
                color=LINE, linewidth=1.5, zorder=1, solid_capstyle="round")
        ax.annotate("", xy=(parts_anchor_x, parent_y), xytext=(corridor, parent_y),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.32,head_length=0.6",
                                    color=LINE, linewidth=1.5, shrinkA=0, shrinkB=2),
                    zorder=1)
        ax.text(corridor, child_y + 0.24, label,
                fontsize=8.6, color=MUTED, ha="center", va="bottom",
                zorder=5, family="DejaVu Sans",
                bbox=dict(boxstyle="round,pad=0.18", facecolor=BG, edgecolor="none"))

    # parts_queue -> parts, тоже без FK
    pqx, pqy, pqw, pqh = boxes["parts_queue"]
    pq_row_y = pqy + pqh - HEAD_H - ROW_H * 0.5
    parts_row_y = ppy + pph - HEAD_H - ROW_H * 0.5
    ax.add_patch(FancyArrowPatch(
        (pqx, pq_row_y), (parts_anchor_x, parts_row_y),
        connectionstyle="arc3,rad=0.14",
        arrowstyle="-|>,head_width=4,head_length=7",
        color="#c0a58b", linewidth=1.5, linestyle=(0, (5, 3)), zorder=1,
        shrinkA=3, shrinkB=3))
    ax.text((pqx + parts_anchor_x) / 2, (pq_row_y + parts_row_y) / 2 - 1.0,
            "1 : 1 логически\n(без FK)", fontsize=8.4, color="#a3846a",
            ha="center", va="center", zorder=5, family="DejaVu Sans",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=BG, edgecolor="none"))

    # связи «дочерняя -> accessories.id»
    apx, apy, apw, aph = boxes["accessories"]
    acc_anchor_x = apx + apw
    for idx, (child, _parent, label) in enumerate(ACC_RELATIONS):
        cx, cy, cw, ch = boxes[child]
        child_y = cy + ch - HEAD_H - ROW_H * 0.5
        parent_y = apy + aph - HEAD_H - ROW_H * 0.5
        corridor = cx - 0.35 - 0.42 * idx
        ax.plot([cx, corridor], [child_y, child_y],
                color=LINE, linewidth=1.5, zorder=1, solid_capstyle="round")
        ax.plot([corridor, corridor], [child_y, parent_y],
                color=LINE, linewidth=1.5, zorder=1, solid_capstyle="round")
        ax.annotate("", xy=(acc_anchor_x, parent_y), xytext=(corridor, parent_y),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.32,head_length=0.6",
                                    color=LINE, linewidth=1.5, shrinkA=0, shrinkB=2),
                    zorder=1)
        ax.text(corridor, child_y + 0.24, label,
                fontsize=8.6, color=MUTED, ha="center", va="bottom",
                zorder=5, family="DejaVu Sans",
                bbox=dict(boxstyle="round,pad=0.18", facecolor=BG, edgecolor="none"))

    aqx, aqy, aqw, aqh = boxes["accessories_queue"]
    aq_row_y = aqy + aqh - HEAD_H - ROW_H * 0.5
    acc_row_y = apy + aph - HEAD_H - ROW_H * 0.5
    ax.add_patch(FancyArrowPatch(
        (aqx, aq_row_y), (acc_anchor_x, acc_row_y),
        connectionstyle="arc3,rad=0.14",
        arrowstyle="-|>,head_width=4,head_length=7",
        color="#c0a58b", linewidth=1.5, linestyle=(0, (5, 3)), zorder=1,
        shrinkA=3, shrinkB=3))
    ax.text((aqx + acc_anchor_x) / 2, (aq_row_y + acc_row_y) / 2 - 1.0,
            "1 : 1 логически\n(без FK)", fontsize=8.4, color="#a3846a",
            ha="center", va="center", zorder=5, family="DejaVu Sans",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=BG, edgecolor="none"))

    ax.text(40.9, 16.45, "АКСЕССУАРЫ · 519", fontsize=11, fontweight="bold",
            color=HEAD_ACC, family="DejaVu Sans")

    # заголовки семейств
    ax.text(0.5, 16.45, "ВЕЛОСИПЕДЫ · 16 176", fontsize=11, fontweight="bold",
            color=HEAD_MAIN, family="DejaVu Sans")
    ax.text(24.8, 16.45, "ЗАПЧАСТИ · 1 016", fontsize=11, fontweight="bold",
            color=HEAD_PARTS, family="DejaVu Sans")

    # логическая связь crawl_queue -> bikes (без FK: очередь живёт своей жизнью)
    qx, qy, qw, qh = boxes["crawl_queue"]
    q_row_y = qy + qh - HEAD_H - ROW_H * 0.5
    b_row_y = py + ph - HEAD_H - ROW_H * 0.5
    ax.add_patch(FancyArrowPatch(
        (qx + qw, q_row_y), (px, b_row_y),
        connectionstyle="arc3,rad=-0.12",
        arrowstyle="-|>,head_width=4,head_length=7",
        color="#c0a58b", linewidth=1.5, linestyle=(0, (5, 3)), zorder=1,
        shrinkA=2, shrinkB=2))
    ax.text((qx + qw + px) / 2, (q_row_y + b_row_y) / 2 + 0.55,
            "1 : 1 логически\n(без FK)", fontsize=8.4, color="#a3846a",
            ha="center", va="bottom", zorder=5, family="DejaVu Sans",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=BG, edgecolor="none"))

    ax.text(0.5, 18.25, "velostok — схема базы данных",
            fontsize=19, fontweight="bold", color=TEXT, family="DejaVu Sans")
    ax.text(0.5, 17.72,
            "Товары, спарсенные с velosklad.ru  ·  MySQL 9.3, utf8mb4  ·  16 176 велосипедов, 1 016 запчастей, 519 аксессуаров",
            fontsize=10.5, color=MUTED, family="DejaVu Sans")

    legend = [
        ("#2f7a4f", "PK — первичный ключ"),
        ("#b5651d", "FK — внешний ключ, ON DELETE CASCADE"),
        (MUTED, "idx — индекс"),
    ]
    for i, (color, text) in enumerate(legend):
        ax.text(0.55, 2.35 - i * 0.52, "■", fontsize=10, color=color,
                va="center", family="DejaVu Sans")
        ax.text(1.05, 2.35 - i * 0.52, text, fontsize=9.4, color=TEXT,
                va="center", family="DejaVu Sans")

    ax.text(0.5, -0.35,
            "Каждый раздел каталога живёт в своём семействе таблиц. У велосипедов есть год, класс, пол и ростовки; "
            "у запчастей и аксессуаров вместо них — категория с подкатегорией.\nЗапчасти и аксессуары делят одно "
            "пространство ID на сайте, но с ID велосипедов оно не связано. Характеристики везде хранятся по модели EAV.",
            fontsize=9, color=MUTED, va="bottom", family="DejaVu Sans")

    fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    print(f"схема сохранена: {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "db_schema.png")
