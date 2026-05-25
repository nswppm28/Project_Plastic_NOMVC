# -*- coding: utf-8 -*-
"""
app.py แบบรวมไฟล์เดียว
- รวม backend เดิมทั้งหมดกลับมาไว้ในไฟล์นี้
- templates, static, sql ยังใช้โครงสร้างเดิม
- รันด้วยคำสั่ง: python app.py
"""
import time
from pathlib import Path
import os
import json
import traceback
from datetime import date, datetime
from decimal import Decimal
from functools import wraps

import mysql.connector
from mysql.connector import Error
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

try:
    import numpy as np
except ModuleNotFoundError:
    np = None

try:
    from PIL import Image
except ModuleNotFoundError:
    Image = None

try:
    import tensorflow as tf
except ModuleNotFoundError:
    tf = None


# =========================================================
# APP CONFIG
# =========================================================

app = Flask(__name__)
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.jinja_env.auto_reload = True


@app.context_processor
def inject_asset_version():
    def asset_version(filename):
        file_path = BASE_DIR / "static" / filename

        try:
            return int(file_path.stat().st_mtime)
        except OSError:
            return int(time.time())

    return {
        "asset_version": asset_version
    }


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response 
app.secret_key = os.getenv("FLASK_SECRET_KEY", "plastic-buyback-secret-key")

MYSQL_PASSWORD = os.getenv("DB_PASSWORD") or "Nam640710768"

DB_CONFIG = {
    "host": os.getenv("DB_HOST") or "localhost",
    "user": os.getenv("DB_USER") or "root",
    "password": MYSQL_PASSWORD,
    "database": os.getenv("DB_NAME") or "plastic_buyback_db",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}

print("DB_CONFIG_FILE =", __file__)
print("DB_USER =", DB_CONFIG["user"])
print("DB_PASSWORD_SET =", bool(DB_CONFIG["password"]))
print("DB_NAME =", DB_CONFIG["database"])

MODEL_PATH = os.getenv("MODEL_PATH", "plastic_model.h5")

CLASS_NAMES = ["HDPE", "LDPE", "PET", "PP", "PS", "PVC"]

FULL_NAMES = {
    "HDPE": "High-Density Polyethylene",
    "LDPE": "Low-Density Polyethylene",
    "PET": "Polyethylene Terephthalate",
    "PP": "Polypropylene",
    "PS": "Polystyrene",
    "PVC": "Polyvinyl Chloride",
}

# =========================================================
# GENERAL HELPERS
# =========================================================

def json_ready(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, dict):
        return {k: json_ready(v) for k, v in value.items()}
    return value


def success_response(data=None, message="success", status_code=200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = json_ready(data)
    return jsonify(payload), status_code


def error_response(message="เกิดข้อผิดพลาด", status_code=400, detail=None):
    payload = {"success": False, "error": message}
    if detail:
        payload["detail"] = str(detail)
    return jsonify(payload), status_code


def to_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def to_int(value, default=0):
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def format_datetime_th(value):
    if not value:
        return "-"

    if isinstance(value, str):
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                value = datetime.strptime(value, pattern)
                break
            except ValueError:
                pass
        else:
            return value

    return value.strftime("%d/%m/%Y %H:%M")


def generate_running_no(fetch_one_func, prefix, table_name, column_name):
    year_text = datetime.now().strftime("%Y")
    allowed_targets = {
        ("PU", "purchases", "purchase_no"),
        ("RC", "receipts", "receipt_no"),
    }

    if (prefix, table_name, column_name) not in allowed_targets:
        raise ValueError("Invalid running number target")

    row = fetch_one_func(
        f"""
        SELECT {column_name}
        FROM {table_name}
        WHERE {column_name} LIKE %s
        ORDER BY {column_name} DESC
        LIMIT 1
        """,
        (f"{prefix}-{year_text}-%",),
    )

    if not row or not row.get(column_name):
        return f"{prefix}-{year_text}-0001"

    try:
        seq = int(str(row[column_name]).split("-")[-1]) + 1
    except ValueError:
        seq = 1

    return f"{prefix}-{year_text}-{seq:04d}"


def generate_customer_code(fetch_one_func):
    row = fetch_one_func(
        """
        SELECT customer_code
        FROM customers
        WHERE customer_code LIKE 'CUST-%'
        ORDER BY customer_code DESC
        LIMIT 1
        """
    )

    if not row:
        return "CUST-0001"

    try:
        seq = int(str(row["customer_code"]).split("-")[-1]) + 1
    except ValueError:
        seq = 1

    return f"CUST-{seq:04d}"

# =========================================================
# DECORATORS
# =========================================================

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("กรุณาเข้าสู่ระบบก่อน", "error")
            return redirect(url_for("login_page"))
        return func(*args, **kwargs)
    return wrapper

# =========================================================
# DATABASE HELPERS
# =========================================================

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None, commit=True):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        lastrowid = cursor.lastrowid
        if commit:
            conn.commit()
        return lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_default_user_id():
    try:
        row = fetch_one(
            """
            SELECT user_id
            FROM users
            WHERE is_active = 1
            ORDER BY user_id
            LIMIT 1
            """
        )
        return row["user_id"] if row else None
    except Exception:
        return None

# =========================================================
# SERVICES
# =========================================================


# ----- auth_service.py -----

def authenticate_user(username, password):
    user = fetch_one(
        """
        SELECT *
        FROM users
        WHERE username = %s
          AND is_active = 1
        LIMIT 1
        """,
        (username,),
    )

    if not user:
        return None

    try:
        if check_password_hash(user.get("password_hash"), password):
            return user
    except Exception:
        return None

    return None

# ----- customer_service.py -----

def load_customers():
    return fetch_all(
        """
        SELECT
            c.customer_id AS id,
            c.customer_id,
            c.customer_code,
            c.full_name,
            c.phone,
            c.address,
            c.note,
            COUNT(DISTINCT p.purchase_id) AS visit_count,
            COALESCE(SUM(p.total_amount), 0) AS total_value
        FROM customers c
        LEFT JOIN purchases p
            ON c.customer_id = p.customer_id
        WHERE c.is_active = 1
        GROUP BY
            c.customer_id,
            c.customer_code,
            c.full_name,
            c.phone,
            c.address,
            c.note
        ORDER BY c.customer_id DESC
        """
    )


def get_customer(customer_id):
    return fetch_one("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))


def customer_has_purchases(customer_id):
    row = fetch_one(
        """
        SELECT COUNT(*) AS purchase_count
        FROM purchases
        WHERE customer_id = %s
        """,
        (customer_id,),
    )
    return to_int(row.get("purchase_count") if row else 0) > 0


def create_customer_record(full_name, phone, address, note):
    return execute_query(
        """
        INSERT INTO customers (customer_code, full_name, phone, address, note)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            generate_customer_code(fetch_one),
            full_name,
            phone,
            address,
            note or None,
        ),
    )


def update_customer_record(customer_id, full_name, phone, address, note):
    return execute_query(
        """
        UPDATE customers
        SET full_name = %s,
            phone = %s,
            address = %s,
            note = %s
        WHERE customer_id = %s
        """,
        (full_name, phone, address, note or None, customer_id),
    )


def delete_customer_record(customer_id):
    if customer_has_purchases(customer_id):
        execute_query(
            """
            UPDATE customers
            SET is_active = 0
            WHERE customer_id = %s
            """,
            (customer_id,),
        )
        return "soft_delete"

    execute_query("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
    return "delete"

# ----- dashboard_service.py -----

def load_recent_transactions(limit=10):
    rows = fetch_all(
        """
        SELECT
            p.purchase_id AS id,
            p.purchase_no,
            r.receipt_no,
            p.purchase_date AS purchase_datetime,
            c.customer_code,
            c.full_name AS customer_name,
            COALESCE(
                GROUP_CONCAT(
                    CONCAT(pt.type_code, ' / ', ps.subtype_name)
                    ORDER BY pi.item_id
                    SEPARATOR ', '
                ),
                '-'
            ) AS plastic_label,
            COALESCE(ROUND(SUM(pi.weight_kg), 3), 0) AS weight_kg,
            COALESCE(p.total_amount, 0) AS amount
        FROM purchases p
        INNER JOIN customers c
            ON p.customer_id = c.customer_id
        LEFT JOIN receipts r
            ON p.purchase_id = r.purchase_id
        LEFT JOIN purchase_items pi
            ON p.purchase_id = pi.purchase_id
        LEFT JOIN plastic_subtypes ps
            ON pi.subtype_id = ps.subtype_id
        LEFT JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        GROUP BY
            p.purchase_id,
            p.purchase_no,
            r.receipt_no,
            p.purchase_date,
            c.customer_code,
            c.full_name,
            p.total_amount
        ORDER BY p.purchase_date DESC
        LIMIT %s
        """,
        (limit,),
    )

    for row in rows:
        row["purchase_date"] = format_datetime_th(row.get("purchase_datetime"))

    return rows


def load_dashboard_data():
    daily = fetch_one(
        """
        SELECT
            COUNT(DISTINCT p.purchase_id) AS purchase_count,
            COALESCE(SUM(p.total_amount), 0) AS total_amount
        FROM purchases p
        WHERE DATE(p.purchase_date) = CURDATE()
        """
    ) or {}

    monthly = fetch_one(
        """
        SELECT
            COUNT(DISTINCT p.purchase_id) AS purchase_count,
            COALESCE(SUM(p.total_amount), 0) AS total_amount
        FROM purchases p
        WHERE YEAR(p.purchase_date) = YEAR(CURDATE())
          AND MONTH(p.purchase_date) = MONTH(CURDATE())
        """
    ) or {}

    grand = fetch_one(
        """
        SELECT
            COUNT(DISTINCT p.purchase_id) AS total_documents,
            COALESCE(SUM(p.total_amount), 0) AS grand_total_amount
        FROM purchases p
        """
    ) or {}

    top_plastic = fetch_one(
        """
        SELECT
            pt.type_code,
            pt.type_name_th,
            ROUND(SUM(pi.weight_kg), 3) AS total_weight_kg,
            ROUND(SUM(pi.amount), 2) AS total_amount
        FROM purchase_items pi
        INNER JOIN plastic_subtypes ps
            ON pi.subtype_id = ps.subtype_id
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        GROUP BY pt.type_id, pt.type_code, pt.type_name_th
        ORDER BY total_weight_kg DESC, total_amount DESC
        LIMIT 1
        """
    ) or {}

    top_customer = fetch_one(
        """
        SELECT
            c.full_name,
            COUNT(DISTINCT p.purchase_id) AS purchase_count,
            COALESCE(SUM(p.total_amount), 0) AS total_amount
        FROM purchases p
        INNER JOIN customers c
            ON p.customer_id = c.customer_id
        GROUP BY c.customer_id, c.full_name
        ORDER BY purchase_count DESC, total_amount DESC
        LIMIT 1
        """
    ) or {}

    daily_amount = to_float(daily.get("total_amount"))
    monthly_amount = to_float(monthly.get("total_amount"))
    grand_amount = to_float(grand.get("grand_total_amount"))
    daily_count = to_int(daily.get("purchase_count"))
    monthly_count = to_int(monthly.get("purchase_count"))
    total_documents = to_int(grand.get("total_documents"))

    top_plastic_code = top_plastic.get("type_code") or "-"
    top_plastic_name = top_plastic.get("type_name_th") or ""
    top_plastic_weight = to_float(top_plastic.get("total_weight_kg"))
    top_customer_name = top_customer.get("full_name") or "-"
    top_customer_count = to_int(top_customer.get("purchase_count"))

    return {
        "daily_total": f"฿ {daily_amount:,.2f}",
        "monthly_total": f"฿ {monthly_amount:,.2f}",
        "grand_total": f"฿ {grand_amount:,.2f}",
        "daily_count": f"{daily_count} รายการ",
        "monthly_count": f"{monthly_count} รายการ",
        "total_documents": f"{total_documents} รายการ",
        "top_plastic": top_plastic_code,
        "top_plastic_detail": (
            f"{top_plastic_name} / {top_plastic_weight:,.3f} กก."
            if top_plastic_code != "-"
            else "-"
        ),
        "top_customer": top_customer_name,
        "top_customer_detail": (
            f"ขายทั้งหมด {top_customer_count} ครั้ง"
            if top_customer_name != "-"
            else "-"
        ),
    }


def load_top_plastics(limit=5):
    rows = fetch_all(
        """
        SELECT
            pt.type_code AS plastic_type,
            pt.type_name_th AS plastic_name_th,
            ROUND(SUM(pi.weight_kg), 3) AS total_weight
        FROM purchase_items pi
        INNER JOIN plastic_subtypes ps
            ON pi.subtype_id = ps.subtype_id
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        GROUP BY pt.type_id, pt.type_code, pt.type_name_th
        ORDER BY total_weight DESC
        LIMIT %s
        """,
        (limit,),
    )

    total_weight_all = sum(to_float(item.get("total_weight")) for item in rows)
    top_plastics = []

    for item in rows:
        weight = to_float(item.get("total_weight"))
        percent = (weight / total_weight_all * 100) if total_weight_all > 0 else 0
        top_plastics.append(
            {
                "plastic_type": item.get("plastic_type") or "-",
                "plastic_name_th": item.get("plastic_name_th") or "",
                "total_weight": weight,
                "percent": round(percent, 2),
            }
        )

    return top_plastics

# ----- plastic_service.py -----

def get_type_by_code(type_code):
    return fetch_one(
        """
        SELECT type_id, type_code, type_name_th, type_name_en
        FROM plastic_types
        WHERE type_code = %s
        LIMIT 1
        """,
        (type_code,),
    )


def get_subtypes_by_type_code(type_code):
    return fetch_all(
        """
        SELECT
            pt.type_id,
            pt.type_code,
            ps.subtype_id,
            ps.subtype_code,
            ps.subtype_name,
            pp.unit_price,
            pp.unit_name
        FROM plastic_types pt
        INNER JOIN plastic_subtypes ps
            ON pt.type_id = ps.type_id
        LEFT JOIN purchase_prices pp
            ON pp.subtype_id = ps.subtype_id
           AND pp.is_current = 1
           AND (pp.effective_end_date IS NULL OR pp.effective_end_date >= CURDATE())
        WHERE pt.type_code = %s
          AND pt.is_active = 1
          AND ps.is_active = 1
        ORDER BY ps.subtype_name
        """,
        (type_code,),
    )


def get_current_price_by_subtype(subtype_id):
    return fetch_one(
        """
        SELECT
            pp.price_id,
            pp.subtype_id,
            pp.unit_price,
            pp.unit_name,
            pp.effective_start_date,
            ps.subtype_code,
            ps.subtype_name,
            pt.type_code,
            pt.type_name_th,
            pt.type_name_en
        FROM purchase_prices pp
        INNER JOIN plastic_subtypes ps
            ON pp.subtype_id = ps.subtype_id
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        WHERE pp.subtype_id = %s
          AND pp.is_current = 1
          AND (pp.effective_end_date IS NULL OR pp.effective_end_date >= CURDATE())
        ORDER BY pp.effective_start_date DESC, pp.price_id DESC
        LIMIT 1
        """,
        (subtype_id,),
    )


def load_catalog():
    rows = fetch_all(
        """
        SELECT
            pt.type_id,
            pt.type_code,
            pt.type_name_th,
            pt.type_name_en,
            ps.subtype_id,
            ps.subtype_code,
            ps.subtype_name,
            COALESCE(pp.unit_price, 0) AS unit_price
        FROM plastic_types pt
        LEFT JOIN plastic_subtypes ps
            ON pt.type_id = ps.type_id
           AND ps.is_active = 1
        LEFT JOIN purchase_prices pp
            ON ps.subtype_id = pp.subtype_id
           AND pp.is_current = 1
        WHERE pt.is_active = 1
        ORDER BY
            FIELD(pt.type_code, 'PET', 'HDPE', 'PVC', 'LDPE', 'PP', 'PS'),
            pt.type_code ASC,
            ps.subtype_name ASC
        """
    )

    catalog_dict = {}

    for row in rows:
        type_id = row["type_id"]

        if type_id not in catalog_dict:
            catalog_dict[type_id] = {
                "id": row["type_id"],
                "type_id": row["type_id"],
                "code": row["type_code"],
                "type_code": row["type_code"],
                "type_name_th": row["type_name_th"],
                "type_name_en": row["type_name_en"],
                "full_name": row["type_name_en"],
                "subtypes": [],
            }

        if row["subtype_id"] is not None:
            catalog_dict[type_id]["subtypes"].append(
                {
                    "id": row["subtype_id"],
                    "subtype_id": row["subtype_id"],
                    "code": row["subtype_code"],
                    "subtype_code": row["subtype_code"],
                    "name": row["subtype_name"],
                    "subtype_name": row["subtype_name"],
                    "price": row["unit_price"],
                    "unit_price": row["unit_price"],
                }
            )

    return list(catalog_dict.values())


def get_active_plastic_types():
    return fetch_all(
        """
        SELECT type_id, type_code, type_name_th
        FROM plastic_types
        WHERE is_active = 1
        ORDER BY type_code
        """
    )


def get_plastic_subtype(subtype_id):
    return fetch_one(
        """
        SELECT ps.*, pt.type_code, pt.type_name_en, pt.type_name_th
        FROM plastic_subtypes ps
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        WHERE ps.subtype_id = %s
        """,
        (subtype_id,),
    )


def create_plastic_subtype_record(type_id, subtype_code, subtype_name, description, unit_price):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO plastic_subtypes (type_id, subtype_code, subtype_name, description)
            VALUES (%s, %s, %s, %s)
            """,
            (type_id, subtype_code, subtype_name, description or None),
        )

        subtype_id = cursor.lastrowid

        if unit_price is not None:
            cursor.execute(
                """
                INSERT INTO purchase_prices (
                    subtype_id, unit_price, unit_name, effective_start_date,
                    effective_end_date, is_current, reference_source, updated_by
                )
                VALUES (%s, %s, 'บาท/กก.', CURDATE(), NULL, 1, %s, %s)
                """,
                (subtype_id, unit_price, "เพิ่มจากระบบ", get_default_user_id()),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def update_plastic_subtype_record(subtype_id, subtype_name, description, is_active):
    execute_query(
        """
        UPDATE plastic_subtypes
        SET subtype_name = %s,
            description = %s,
            is_active = %s
        WHERE subtype_id = %s
        """,
        (subtype_name, description or None, is_active, subtype_id),
    )


def delete_plastic_subtype_record(subtype_id):
    execute_query("DELETE FROM plastic_subtypes WHERE subtype_id = %s", (subtype_id,))


def update_purchase_price_record(subtype_id, unit_price):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE purchase_prices
            SET is_current = 0,
                effective_end_date = CURDATE()
            WHERE subtype_id = %s
              AND is_current = 1
            """,
            (subtype_id,),
        )

        cursor.execute(
            """
            INSERT INTO purchase_prices (
                subtype_id, unit_price, unit_name, effective_start_date,
                effective_end_date, is_current, reference_source, updated_by
            )
            VALUES (%s, %s, 'บาท/กก.', CURDATE(), NULL, 1, %s, %s)
            """,
            (subtype_id, unit_price, "อัปเดตราคาจากหน้าเว็บ", get_default_user_id()),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

# ----- receipt_service.py -----

def load_receipt_history(keyword=""):
    like_keyword = f"%{keyword}%"

    rows = fetch_all(
        """
        SELECT
            p.purchase_id,
            p.purchase_no,
            r.receipt_no,
            p.purchase_date AS receipt_datetime,
            c.customer_id,
            c.customer_code,
            c.full_name AS customer_name,
            c.phone,
            COALESCE(ROUND(SUM(pi.weight_kg), 3), 0) AS total_weight_kg,
            COALESCE(p.total_amount, 0) AS total_amount,
            COALESCE(
                GROUP_CONCAT(
                    DISTINCT pt.type_code
                    ORDER BY pt.type_code
                    SEPARATOR ', '
                ),
                '-'
            ) AS plastic_types
        FROM purchases p
        INNER JOIN customers c
            ON p.customer_id = c.customer_id
        LEFT JOIN receipts r
            ON p.purchase_id = r.purchase_id
        LEFT JOIN purchase_items pi
            ON p.purchase_id = pi.purchase_id
        LEFT JOIN plastic_subtypes ps
            ON pi.subtype_id = ps.subtype_id
        LEFT JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        WHERE
            (
                %s = ''
                OR c.full_name LIKE %s
                OR c.phone LIKE %s
                OR c.customer_code LIKE %s
                OR p.purchase_no LIKE %s
                OR r.receipt_no LIKE %s
            )
        GROUP BY
            p.purchase_id,
            p.purchase_no,
            r.receipt_no,
            p.purchase_date,
            c.customer_id,
            c.customer_code,
            c.full_name,
            c.phone,
            p.total_amount
        ORDER BY p.purchase_date DESC
        """,
        (keyword, like_keyword, like_keyword, like_keyword, like_keyword, like_keyword),
    )

    for row in rows:
        row["receipt_date"] = format_datetime_th(row.get("receipt_datetime"))

    return rows


def load_receipt_data(purchase_id):
    receipt = fetch_one(
        """
        SELECT
            r.receipt_id,
            r.receipt_no,
            r.printed_at AS printed_datetime,
            p.purchase_date AS receipt_datetime,
            p.purchase_id,
            p.purchase_no,
            c.customer_id,
            c.customer_code,
            c.full_name AS customer_name,
            c.phone,
            c.address,
            p.total_amount,
            p.payment_method,
            p.note
        FROM receipts r
        INNER JOIN purchases p
            ON r.purchase_id = p.purchase_id
        INNER JOIN customers c
            ON p.customer_id = c.customer_id
        WHERE p.purchase_id = %s
        LIMIT 1
        """,
        (purchase_id,),
    )

    receipt_items = fetch_all(
        """
        SELECT
            pi.item_id,
            pt.type_code,
            ps.subtype_code,
            CONCAT(pt.type_code, ' / ', ps.subtype_name) AS subtype_name,
            ps.subtype_name AS subtype_name_only,
            pi.weight_kg,
            pi.unit_price,
            pi.amount,
            pi.image_path,
            pi.confirmed_by_user
        FROM purchase_items pi
        INNER JOIN plastic_subtypes ps
            ON pi.subtype_id = ps.subtype_id
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        WHERE pi.purchase_id = %s
        ORDER BY pi.item_id
        """,
        (purchase_id,),
    ) if receipt else []

    if receipt:
        receipt["printed_at"] = format_datetime_th(receipt.get("printed_datetime"))
        receipt["receipt_date"] = format_datetime_th(receipt.get("receipt_datetime"))

    return receipt, receipt_items

# ----- stock_service.py -----

def load_stock_items():
    """
    โหลดข้อมูลสต๊อกคงเหลือของพลาสติกทุกประเภทย่อย
    ใช้ LEFT JOIN เพื่อให้เห็นรายการที่ยังไม่มี stock_summary เป็น 0 กก.
    """
    rows = fetch_all(
        """
        SELECT
            pt.type_code,
            pt.type_name_th,
            ps.subtype_id,
            ps.subtype_code,
            ps.subtype_name,
            COALESCE(ss.total_weight_kg, 0) AS total_weight,
            COALESCE(ss.total_weight_kg, 0) AS total_weight_kg,
            ss.last_in_datetime,
            ss.updated_at
        FROM plastic_subtypes ps
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        LEFT JOIN stock_summary ss
            ON ps.subtype_id = ss.subtype_id
        WHERE ps.is_active = 1
          AND pt.is_active = 1
        ORDER BY
            FIELD(pt.type_code, 'PET', 'HDPE', 'PVC', 'LDPE', 'PP', 'PS'),
            pt.type_code,
            ps.subtype_name
        """
    )

    for row in rows:
        weight = to_float(row.get("total_weight_kg"))

        row["total_weight"] = weight
        row["total_weight_kg"] = weight
        row["last_in_datetime"] = format_datetime_th(row.get("last_in_datetime"))
        row["updated_at"] = format_datetime_th(row.get("updated_at"))

    return rows


def load_stock_movements(limit=50):
    """
    โหลดประวัติการเคลื่อนไหวของสต๊อกล่าสุด
    ใช้สำหรับตารางด้านล่างของหน้า Stock
    """
    rows = fetch_all(
        """
        SELECT
            sm.movement_id,
            sm.subtype_id,
            sm.purchase_item_id,
            sm.movement_type,
            sm.quantity_kg,
            sm.balance_after_kg,
            sm.note,
            sm.created_at,
            pt.type_code,
            pt.type_name_th,
            ps.subtype_code,
            ps.subtype_name
        FROM stock_movements sm
        INNER JOIN plastic_subtypes ps
            ON sm.subtype_id = ps.subtype_id
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        ORDER BY sm.created_at DESC, sm.movement_id DESC
        LIMIT %s
        """,
        (limit,),
    )

    for row in rows:
        row["quantity_kg"] = to_float(row.get("quantity_kg"))
        row["balance_after_kg"] = to_float(row.get("balance_after_kg"))
        row["created_at"] = format_datetime_th(row.get("created_at"))

    return rows

# ----- stock_export_service.py -----

def load_stock_buyers():
    return fetch_all(
        """
        SELECT
            buyer_id,
            buyer_code,
            buyer_name,
            buyer_type,
            phone,
            contact_person,
            address,
            note
        FROM stock_buyers
        WHERE is_active = 1
        ORDER BY buyer_name ASC
        """
    )


def get_stock_status(weight_kg):
    weight = to_float(weight_kg)

    if weight >= 100:
        return "พร้อมจำหน่าย"

    if weight >= 50:
        return "ปริมาณปานกลาง"

    if weight > 0:
        return "ปริมาณน้อย"

    return "ไม่มีสินค้า"


def load_exportable_stock_items():
    rows = fetch_all(
        """
        SELECT
            pt.type_code,
            pt.type_name_th,
            ps.subtype_id,
            ps.subtype_code,
            ps.subtype_name,
            COALESCE(ss.total_weight_kg, 0) AS total_weight_kg,
            COALESCE(pp.unit_price, 0) AS purchase_price
        FROM plastic_subtypes ps
        INNER JOIN plastic_types pt
            ON ps.type_id = pt.type_id
        LEFT JOIN stock_summary ss
            ON ps.subtype_id = ss.subtype_id
        LEFT JOIN purchase_prices pp
            ON pp.subtype_id = ps.subtype_id
           AND pp.is_current = 1
           AND (pp.effective_end_date IS NULL OR pp.effective_end_date >= CURDATE())
        WHERE ps.is_active = 1
          AND pt.is_active = 1
          AND COALESCE(ss.total_weight_kg, 0) > 0
        ORDER BY
            FIELD(pt.type_code, 'PET', 'HDPE', 'PVC', 'LDPE', 'PP', 'PS'),
            pt.type_code,
            ps.subtype_name
        """
    )

    for row in rows:
        weight = to_float(row.get("total_weight_kg"))
        purchase_price = to_float(row.get("purchase_price"))

        row["total_weight_kg"] = weight
        row["purchase_price"] = purchase_price
        row["suggested_export_price"] = round(purchase_price + 2, 2) if purchase_price > 0 else 0
        row["status_text"] = get_stock_status(weight)

    return rows


def generate_export_no(cursor):
    cursor.execute(
        """
        SELECT export_no
        FROM stock_exports
        WHERE export_no LIKE CONCAT('EXP-', YEAR(CURDATE()), '-%')
        ORDER BY export_no DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()
    year_text = __import__("datetime").datetime.now().strftime("%Y")

    if not row or not row.get("export_no"):
        return f"EXP-{year_text}-0001"

    try:
        seq = int(str(row["export_no"]).split("-")[-1]) + 1
    except ValueError:
        seq = 1

    return f"EXP-{year_text}-{seq:04d}"


def create_stock_export_record(
    buyer_id,
    subtype_id,
    weight_kg,
    unit_price,
    transport_method=None,
    vehicle_plate=None,
    note=None,
    created_by=None,
):
    buyer_id = to_int(buyer_id)
    subtype_id = to_int(subtype_id)
    weight_kg = to_float(weight_kg)
    unit_price = to_float(unit_price)

    if not buyer_id:
        raise ValueError("กรุณาเลือกผู้รับซื้อปลายทาง")

    if not subtype_id:
        raise ValueError("กรุณาเลือกพลาสติกที่ต้องการจำหน่ายออก")

    if weight_kg <= 0:
        raise ValueError("น้ำหนักจำหน่ายออกต้องมากกว่า 0 กก.")

    if unit_price <= 0:
        raise ValueError("ราคาขายต่อกิโลกรัมต้องมากกว่า 0 บาท")

    amount = round(weight_kg * unit_price, 2)
    use_export_trigger = has_stock_export_trigger()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT buyer_id
            FROM stock_buyers
            WHERE buyer_id = %s
              AND is_active = 1
            LIMIT 1
            """,
            (buyer_id,),
        )

        if not cursor.fetchone():
            raise ValueError("ไม่พบข้อมูลผู้รับซื้อปลายทาง หรือผู้รับซื้อถูกปิดใช้งาน")

        cursor.execute(
            """
            SELECT
                ss.total_weight_kg,
                ps.subtype_name,
                pt.type_code
            FROM stock_summary ss
            INNER JOIN plastic_subtypes ps
                ON ss.subtype_id = ps.subtype_id
            INNER JOIN plastic_types pt
                ON ps.type_id = pt.type_id
            WHERE ss.subtype_id = %s
            FOR UPDATE
            """,
            (subtype_id,),
        )

        stock_row = cursor.fetchone()

        if not stock_row:
            raise ValueError("ไม่พบสินค้าในคลังสำหรับประเภทย่อยนี้")

        current_weight = to_float(stock_row.get("total_weight_kg"))

        if current_weight < weight_kg:
            raise ValueError(
                f"จำนวนสินค้าในคลังไม่เพียงพอ มีคงเหลือ {current_weight:.2f} กก."
            )

        export_no = generate_export_no(cursor)

        cursor.execute(
            """
            INSERT INTO stock_exports (
                export_no,
                buyer_id,
                export_date,
                total_weight_kg,
                total_amount,
                transport_method,
                vehicle_plate,
                status,
                note,
                created_by
            )
            VALUES (%s, %s, NOW(), 0.000, 0.00, %s, %s, 'completed', %s, %s)
            """,
            (
                export_no,
                buyer_id,
                transport_method or None,
                vehicle_plate or None,
                note or None,
                created_by,
            ),
        )

        export_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO stock_export_items (
                export_id,
                subtype_id,
                weight_kg,
                unit_price,
                amount,
                note
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                export_id,
                subtype_id,
                weight_kg,
                unit_price,
                amount,
                note or None,
            ),
        )

        export_item_id = cursor.lastrowid

        if not use_export_trigger:
            new_balance = round(current_weight - weight_kg, 3)

            cursor.execute(
                """
                UPDATE stock_summary
                SET total_weight_kg = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE subtype_id = %s
                """,
                (new_balance, subtype_id),
            )

            cursor.execute(
                """
                UPDATE stock_exports
                SET total_weight_kg = %s,
                    total_amount = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE export_id = %s
                """,
                (weight_kg, amount, export_id),
            )

            cursor.execute(
                """
                INSERT INTO stock_movements (
                    subtype_id,
                    purchase_item_id,
                    stock_export_item_id,
                    movement_type,
                    quantity_kg,
                    balance_after_kg,
                    note,
                    created_at
                )
                VALUES (%s, NULL, %s, 'SALE_OUT', %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (
                    subtype_id,
                    export_item_id,
                    weight_kg * -1,
                    new_balance,
                    f"จำหน่ายออกเลขที่ {export_no}",
                ),
            )

        conn.commit()

        return {
            "export_id": export_id,
            "export_no": export_no,
            "weight_kg": weight_kg,
            "unit_price": unit_price,
            "amount": amount,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def load_stock_export_history(keyword=""):
    keyword = (keyword or "").strip()

    rows = fetch_all(
        """
        SELECT
            se.export_id,
            se.export_no,
            se.export_date,
            se.total_weight_kg,
            se.total_amount,
            se.transport_method,
            se.vehicle_plate,
            se.status,
            se.note,
            sb.buyer_code,
            sb.buyer_name,
            COUNT(sei.export_item_id) AS item_count
        FROM stock_exports se
        INNER JOIN stock_buyers sb
            ON se.buyer_id = sb.buyer_id
        LEFT JOIN stock_export_items sei
            ON se.export_id = sei.export_id
        WHERE
            %s = ''
            OR se.export_no LIKE CONCAT('%%', %s, '%%')
            OR sb.buyer_name LIKE CONCAT('%%', %s, '%%')
            OR sb.buyer_code LIKE CONCAT('%%', %s, '%%')
        GROUP BY
            se.export_id,
            se.export_no,
            se.export_date,
            se.total_weight_kg,
            se.total_amount,
            se.transport_method,
            se.vehicle_plate,
            se.status,
            se.note,
            sb.buyer_code,
            sb.buyer_name
        ORDER BY se.export_date DESC, se.export_id DESC
        LIMIT 100
        """,
        (keyword, keyword, keyword, keyword),
    )

    for row in rows:
        row["export_date"] = format_datetime_th(row.get("export_date"))
        row["total_weight_kg"] = to_float(row.get("total_weight_kg"))
        row["total_amount"] = to_float(row.get("total_amount"))

    return rows

# ----- purchase_service.py -----

def has_trigger(trigger_name):
    row = fetch_one(
        """
        SELECT COUNT(*) AS trigger_count
        FROM information_schema.TRIGGERS
        WHERE TRIGGER_SCHEMA = DATABASE()
          AND TRIGGER_NAME = %s
        """,
        (trigger_name,),
    )
    return bool(row and row.get("trigger_count", 0) > 0)


def has_stock_trigger():
    return has_trigger("trg_purchase_items_after_insert")


def has_stock_export_trigger():
    return has_trigger("trg_stock_export_items_after_insert")


def normalize_purchase_items(items):
    if not isinstance(items, list) or not items:
        raise ValueError("กรุณาเพิ่มรายการลงบิลก่อน")

    normalized = []

    for index, item in enumerate(items, start=1):
        subtype_id = to_int(item.get("subtype_id"))
        weight_kg = to_float(item.get("weight_kg"))

        if not subtype_id or weight_kg <= 0:
            raise ValueError(f"รายการที่ {index} ไม่ถูกต้อง กรุณาเลือกประเภทย่อยและกรอกน้ำหนักมากกว่า 0")

        normalized.append({"subtype_id": subtype_id, "weight_kg": weight_kg})

    return normalized


def update_stock_without_trigger(cursor, subtype_id, purchase_item_id, weight_kg, purchase_no):
    cursor.execute(
        """
        INSERT INTO stock_summary (
            subtype_id,
            total_weight_kg,
            last_in_datetime,
            updated_at
        )
        VALUES (%s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            total_weight_kg = total_weight_kg + VALUES(total_weight_kg),
            last_in_datetime = VALUES(last_in_datetime),
            updated_at = CURRENT_TIMESTAMP
        """,
        (subtype_id, weight_kg),
    )

    cursor.execute(
        """
        SELECT total_weight_kg
        FROM stock_summary
        WHERE subtype_id = %s
        """,
        (subtype_id,),
    )

    stock_row = cursor.fetchone()
    balance_after_kg = stock_row["total_weight_kg"] if stock_row else weight_kg

    cursor.execute(
        """
        INSERT INTO stock_movements (
            subtype_id,
            purchase_item_id,
            movement_type,
            quantity_kg,
            balance_after_kg,
            note
        )
        VALUES (%s, %s, 'PURCHASE_IN', %s, %s, %s)
        """,
        (subtype_id, purchase_item_id, weight_kg, balance_after_kg, f"รับเข้าจากรายการซื้อเลขที่ {purchase_no}"),
    )


def create_purchase_bill_record(customer_id, items):
    items = normalize_purchase_items(items)
    purchase_no = generate_running_no(fetch_one, "PU", "purchases", "purchase_no")
    receipt_no = generate_running_no(fetch_one, "RC", "receipts", "receipt_no")
    user_id = get_default_user_id()
    use_trigger = has_stock_trigger()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO purchases (
                purchase_no,
                customer_id,
                purchase_date,
                total_amount,
                payment_method,
                note,
                created_by
            )
            VALUES (%s, %s, NOW(), 0.00, 'cash', %s, %s)
            """,
            (purchase_no, customer_id, "บันทึกจากหน้าเว็บ", user_id),
        )

        purchase_id = cursor.lastrowid
        total_amount = 0
        saved_items = []

        for item in items:
            subtype_id = item["subtype_id"]
            weight_kg = item["weight_kg"]
            price_row = get_current_price_by_subtype(subtype_id)

            if not price_row:
                raise ValueError(f"ไม่พบราคาปัจจุบันของประเภทย่อย ID {subtype_id}")

            unit_price = to_float(price_row["unit_price"])
            amount = round(weight_kg * unit_price, 2)
            total_amount += amount

            cursor.execute(
                """
                INSERT INTO purchase_items (
                    purchase_id,
                    subtype_id,
                    weight_kg,
                    unit_price,
                    amount,
                    image_path,
                    confirmed_by_user
                )
                VALUES (%s, %s, %s, %s, %s, NULL, 1)
                """,
                (purchase_id, subtype_id, weight_kg, unit_price, amount),
            )

            purchase_item_id = cursor.lastrowid

            if not use_trigger:
                update_stock_without_trigger(cursor, subtype_id, purchase_item_id, weight_kg, purchase_no)

            saved_items.append(
                {
                    "purchase_item_id": purchase_item_id,
                    "subtype_id": subtype_id,
                    "weight_kg": weight_kg,
                    "unit_price": unit_price,
                    "amount": amount,
                }
            )

        cursor.execute(
            """
            UPDATE purchases
            SET total_amount = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE purchase_id = %s
            """,
            (total_amount, purchase_id),
        )

        cursor.execute(
            """
            INSERT INTO receipts (
                purchase_id,
                receipt_no,
                printed_at,
                printed_by,
                status
            )
            VALUES (%s, %s, NOW(), %s, 'printed')
            """,
            (purchase_id, receipt_no, user_id),
        )

        conn.commit()

        return {
            "purchase_id": purchase_id,
            "purchase_no": purchase_no,
            "receipt_no": receipt_no,
            "total_amount": total_amount,
            "items": saved_items,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def create_purchase_record(customer_id, subtype_id, weight_kg):
    return create_purchase_bill_record(
        customer_id=customer_id,
        items=[{"subtype_id": subtype_id, "weight_kg": weight_kg}],
    )

# ----- ai_service.py -----

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_FILE_PATH = MODEL_PATH if os.path.isabs(MODEL_PATH) else os.path.join(BASE_DIR, MODEL_PATH)

model = None
MODEL_LOADED = False
MODEL_ERROR = None


def _load_keras_model(model_path):
    """
    รองรับ TensorFlow/Keras หลายเวอร์ชัน
    บางเวอร์ชันรับ safe_mode=False บางเวอร์ชันไม่รับ
    """
    try:
        return tf.keras.models.load_model(
            model_path,
            compile=False,
            safe_mode=False,
        )
    except TypeError:
        return tf.keras.models.load_model(
            model_path,
            compile=False,
        )


def load_ai_model():
    global model, MODEL_LOADED, MODEL_ERROR

    if tf is None:
        model = None
        MODEL_LOADED = False
        MODEL_ERROR = "ยังไม่ได้ติดตั้ง TensorFlow กรุณาติดตั้งด้วยคำสั่ง pip install tensorflow"
        return

    if Image is None:
        model = None
        MODEL_LOADED = False
        MODEL_ERROR = "ยังไม่ได้ติดตั้ง Pillow กรุณาติดตั้งด้วยคำสั่ง pip install pillow"
        return

    if np is None:
        model = None
        MODEL_LOADED = False
        MODEL_ERROR = "ยังไม่ได้ติดตั้ง NumPy กรุณาติดตั้งด้วยคำสั่ง pip install numpy"
        return

    if not os.path.exists(MODEL_FILE_PATH):
        model = None
        MODEL_LOADED = False
        MODEL_ERROR = f"ไม่พบไฟล์โมเดล: {MODEL_FILE_PATH}"
        return

    try:
        model = _load_keras_model(MODEL_FILE_PATH)
        MODEL_LOADED = True
        MODEL_ERROR = None
        print(f"[AI] โหลดโมเดลสำเร็จ: {MODEL_FILE_PATH}")

    except Exception as e:
        model = None
        MODEL_LOADED = False
        MODEL_ERROR = f"โหลดโมเดลไม่สำเร็จ: {e}"
        print(f"[AI] โหลดโมเดลไม่สำเร็จ: {e}")


load_ai_model()


def get_model_status():
    """
    คงรูปแบบเดิมไว้ เพราะ main_controller.py เดิมใช้:
    model_loaded, model_error = get_model_status()
    """
    return MODEL_LOADED, MODEL_ERROR


def get_model_status_detail():
    """
    ใช้สำหรับ debug ผ่าน /api/ai_status
    """
    return {
        "model_loaded": MODEL_LOADED,
        "model_error": MODEL_ERROR,
        "model_path": MODEL_FILE_PATH,
        "model_file_exists": os.path.exists(MODEL_FILE_PATH),
        "tensorflow_ready": tf is not None,
        "pillow_ready": Image is not None,
        "numpy_ready": np is not None,
        "class_names": CLASS_NAMES,
    }


def preprocess_image(file_storage):
    if Image is None:
        raise RuntimeError("ยังไม่ได้ติดตั้ง Pillow")

    if np is None:
        raise RuntimeError("ยังไม่ได้ติดตั้ง NumPy")

    try:
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream).convert("RGB")
    except Exception as e:
        raise RuntimeError(f"เปิดไฟล์รูปภาพไม่สำเร็จ: {e}")

    image = image.resize((224, 224))
    image_array = np.array(image, dtype=np.float32)

    # หมายเหตุ:
    # EfficientNetB0 ของ Keras มักมี preprocessing อยู่ในตัวโมเดลแล้ว
    # จึงยังไม่หาร 255 ตรงนี้ เพื่อให้ตรงกับตอนเทรนส่วนใหญ่
    return np.expand_dims(image_array, axis=0)


def predict_plastic_from_file(image_file):
    if not MODEL_LOADED or model is None:
        raise RuntimeError(MODEL_ERROR or "โมเดลยังไม่พร้อมใช้งาน")

    input_tensor = preprocess_image(image_file)

    try:
        predictions = model.predict(input_tensor, verbose=0)
    except Exception as e:
        raise RuntimeError(f"โมเดลทำนายรูปภาพไม่สำเร็จ: {e}")

    predictions = np.asarray(predictions)

    if predictions.ndim == 2:
        predictions = predictions[0]

    if predictions.size == 0:
        raise RuntimeError("โมเดลไม่ส่งผลลัพธ์กลับมา")

    predicted_index = int(np.argmax(predictions))

    if predicted_index < len(CLASS_NAMES):
        predicted_label = CLASS_NAMES[predicted_index]
    else:
        predicted_label = f"class_{predicted_index}"

    confidence = float(predictions[predicted_index] * 100)

    scores = []

    for index, score in enumerate(predictions):
        if index < len(CLASS_NAMES):
            label = CLASS_NAMES[index]
        else:
            label = f"class_{index}"

        scores.append(
            {
                "class_name": label,
                "full_name": FULL_NAMES.get(label, label),
                "score": round(float(score * 100), 2),
            }
        )

    scores = sorted(scores, key=lambda item: item["score"], reverse=True)

    predicted_type = None
    subtype_suggestions = []
    database_warning = None

    try:
        predicted_type = get_type_by_code(predicted_label)
        subtype_suggestions = get_subtypes_by_type_code(predicted_label)
    except Exception as e:
        database_warning = str(e)

    return {
        "success": True,
        "plastic_type": predicted_label,
        "plastic_full_name": FULL_NAMES.get(predicted_label, predicted_label),
        "confidence": round(confidence, 2),
        "scores": scores,
        "predicted_type": predicted_type,
        "subtype_suggestions": subtype_suggestions,
        "model_loaded": MODEL_LOADED,
        "database_warning": database_warning,
    }

# =========================================================
# ROUTES
# =========================================================


# ----- auth_controller.py -----

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if "user_id" in session:
        return redirect(url_for("dashboard_page"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน", "error")
            return render_template("login.html")

        user = authenticate_user(username, password)

        if not user:
            flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", "error")
            return render_template("login.html")

        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]

        return redirect(url_for("dashboard_page"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "success")
    return redirect(url_for("login_page"))

# ----- main_controller.py -----

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return redirect(url_for("dashboard_page"))

@app.route("/dashboard")
@login_required
def dashboard_page():
    dashboard = load_dashboard_data()
    transactions = load_recent_transactions()
    top_plastics = load_top_plastics()

    return render_template(
        "dashboard.html",
        current_page="dashboard",
        dashboard=dashboard,
        transactions=transactions,
        top_plastics=top_plastics,
    )

@app.route("/purchase")
@login_required
def purchase_page():
    customers = load_customers()
    catalog = load_catalog()

    return render_template(
        "purchase.html",
        current_page="purchase",
        customers=customers,
        catalog=catalog,
    )

@app.route("/stock")
@login_required
def stock_page():
    stock_items = load_stock_items()
    stock_movements = load_stock_movements()

    return render_template(
        "stock.html",
        current_page="stock",
        stock_items=stock_items,
        stock_movements=stock_movements,
    )

@app.route("/receipt-history")
@login_required
def receipt_history_page():
    keyword = request.args.get("q", "").strip()
    receipt_history = load_receipt_history(keyword)

    return render_template(
        "receipt_history.html",
        current_page="receipt",
        receipt_history=receipt_history,
        receipt_search=keyword,
    )

@app.route("/receipt")
@login_required
def receipt_page():
    purchase_id = request.args.get("purchase_id", type=int)

    if not purchase_id:
        flash("กรุณาเลือกใบเสร็จจากหน้าประวัติย้อนหลัง", "error")
        return redirect(url_for("receipt_history_page"))

    receipt, receipt_items = load_receipt_data(purchase_id)

    if not receipt:
        flash("ไม่พบข้อมูลใบเสร็จ", "error")
        return redirect(url_for("receipt_history_page"))

    return render_template(
        "receipt.html",
        current_page="receipt",
        receipt=receipt,
        receipt_items=receipt_items,
    )

@app.route("/ai-detection")
@login_required
def ai_page():
    model_loaded, model_error = get_model_status()

    return render_template(
        "ai.html",
        current_page="ai",
        model_loaded=model_loaded,
        model_error=model_error,
    )

# ----- customer_controller.py -----

@app.route("/customers")
@login_required
def customers_page():
    customers = load_customers()
    return render_template("customers.html", current_page="customers", customers=customers)

@app.route("/customers/create", methods=["POST"])
@login_required
def create_customer():
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    note = request.form.get("note", "").strip()

    if not full_name or not phone:
        flash("กรุณากรอกชื่อและเบอร์โทรให้ครบ", "error")
        return redirect(url_for("customers_page"))

    create_customer_record(full_name, phone, address, note)
    flash("เพิ่มลูกค้าเรียบร้อยแล้ว", "success")
    return redirect(url_for("customers_page"))

@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        note = request.form.get("note", "").strip()

        update_customer_record(customer_id, full_name, phone, address, note)
        flash("แก้ไขข้อมูลลูกค้าเรียบร้อยแล้ว", "success")
        return redirect(url_for("customers_page"))

    customer = get_customer(customer_id)
    if not customer:
        flash("ไม่พบข้อมูลลูกค้า", "error")
        return redirect(url_for("customers_page"))

    return render_template("customer_edit.html", current_page="customers", customer=customer)

@app.route("/customers/<int:customer_id>/delete")
@login_required
def delete_customer(customer_id):
    customer = get_customer(customer_id)

    if not customer:
        flash("ไม่พบข้อมูลลูกค้า", "error")
        return redirect(url_for("customers_page"))

    try:
        delete_type = delete_customer_record(customer_id)
        if delete_type == "soft_delete":
            flash("ลบลูกค้าออกจากหน้าจัดการแล้ว โดยยังเก็บประวัติรายการรับซื้อและใบเสร็จไว้", "success")
        else:
            flash("ลบข้อมูลลูกค้าเรียบร้อยแล้ว", "success")
    except Error as e:
        flash(f"ไม่สามารถลบลูกค้าได้: {e}", "error")

    return redirect(url_for("customers_page"))

# ----- plastic_controller.py -----

@app.route("/plastic-types")
@login_required
def plastic_types_page():
    catalog = load_catalog()
    return render_template("plastic_types.html", current_page="plastic_types", catalog=catalog)

@app.route("/plastic-types/create", methods=["GET", "POST"])
@login_required
def create_plastic_subtype():
    if request.method == "POST":
        type_id = request.form.get("type_id", type=int)
        subtype_code = request.form.get("subtype_code", "").strip()
        subtype_name = request.form.get("subtype_name", "").strip()
        description = request.form.get("description", "").strip()
        unit_price = request.form.get("unit_price", type=float)

        if not type_id or not subtype_code or not subtype_name:
            flash("กรุณากรอกข้อมูลประเภทย่อยให้ครบ", "error")
            return redirect(url_for("plastic_types_page"))

        try:
            create_plastic_subtype_record(type_id, subtype_code, subtype_name, description, unit_price)
            flash("เพิ่มประเภทย่อยเรียบร้อยแล้ว", "success")
        except Error as e:
            flash(f"เกิดข้อผิดพลาด: {e}", "error")

        return redirect(url_for("plastic_types_page"))

    types = get_active_plastic_types()
    options = "".join(
        [
            f"<option value='{item['type_id']}'>{item['type_code']} - {item['type_name_th']}</option>"
            for item in types
        ]
    )

    return f"""
    <h2>เพิ่มประเภทย่อยพลาสติก</h2>
    <form method="post">
      <label>ประเภทหลัก</label><br>
      <select name="type_id">{options}</select><br><br>
      <input name="subtype_code" placeholder="รหัสประเภทย่อย เช่น PET-CLEAR"><br><br>
      <input name="subtype_name" placeholder="ชื่อประเภทย่อย"><br><br>
      <input name="description" placeholder="คำอธิบาย"><br><br>
      <input name="unit_price" type="number" step="0.01" placeholder="ราคาปัจจุบัน"><br><br>
      <button type="submit">บันทึก</button>
    </form>
    <br>
    <a href="/plastic-types">กลับ</a>
    """

@app.route("/plastic-types/<int:subtype_id>/edit", methods=["GET", "POST"])
@login_required
def edit_plastic_subtype(subtype_id):
    if request.method == "POST":
        subtype_name = request.form.get("subtype_name", "").strip()
        description = request.form.get("description", "").strip()
        is_active = 1 if request.form.get("is_active") == "1" else 0

        update_plastic_subtype_record(subtype_id, subtype_name, description, is_active)
        flash("แก้ไขประเภทย่อยเรียบร้อยแล้ว", "success")
        return redirect(url_for("plastic_types_page"))

    subtype = get_plastic_subtype(subtype_id)
    if not subtype:
        flash("ไม่พบข้อมูลประเภทย่อย", "error")
        return redirect(url_for("plastic_types_page"))

    return render_template("plastic_type_edit.html", current_page="plastic_types", subtype=subtype)

@app.route("/plastic-types/<int:subtype_id>/delete")
@login_required
def delete_plastic_subtype(subtype_id):
    try:
        delete_plastic_subtype_record(subtype_id)
        flash("ลบประเภทย่อยเรียบร้อยแล้ว", "success")
    except Error:
        flash("ไม่สามารถลบประเภทย่อยได้ เนื่องจากมีข้อมูลอ้างอิงอยู่", "error")

    return redirect(url_for("plastic_types_page"))

@app.route("/plastic-types/<int:subtype_id>/price", methods=["POST"])
@login_required
def update_price(subtype_id):
    unit_price = request.form.get("unit_price", type=float)

    if unit_price is None:
        flash("ราคาที่กรอกไม่ถูกต้อง", "error")
        return redirect(url_for("plastic_types_page"))

    try:
        update_purchase_price_record(subtype_id, unit_price)
        flash("อัปเดตราคารับซื้อเรียบร้อยแล้ว", "success")
    except Error as e:
        flash(f"เกิดข้อผิดพลาดในการอัปเดตราคา: {e}", "error")

    return redirect(url_for("plastic_types_page"))

# ----- purchase_controller.py -----

@app.route("/purchase/create", methods=["POST"])
@login_required
def create_purchase():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    customer_id = request.form.get("customer_id", type=int)
    items_json = request.form.get("items_json", "").strip()

    if not customer_id:
        message = "กรุณาเลือกลูกค้า"
        if is_ajax:
            return error_response(message, 400)
        flash(message, "error")
        return redirect(url_for("purchase_page"))

    try:
        if items_json:
            try:
                items = json.loads(items_json)
            except json.JSONDecodeError:
                raise ValueError("รูปแบบข้อมูลรายการในบิลไม่ถูกต้อง")
            result = create_purchase_bill_record(customer_id, items)
        else:
            subtype_id = request.form.get("subtype_id", type=int)
            weight_kg = request.form.get("weight_kg", type=float)

            if not subtype_id or not weight_kg or weight_kg <= 0:
                raise ValueError("กรุณากรอกข้อมูลการรับซื้อให้ครบถ้วน และน้ำหนักต้องมากกว่า 0")

            result = create_purchase_record(customer_id, subtype_id, weight_kg)

        if is_ajax:
            receipt, receipt_items = load_receipt_data(result["purchase_id"])
            return jsonify(
                json_ready(
                    {
                        "success": True,
                        "message": "บันทึกรายการรับซื้อและสร้างใบเสร็จเรียบร้อยแล้ว",
                        "purchase_id": result["purchase_id"],
                        "purchase_no": result["purchase_no"],
                        "receipt_no": result["receipt_no"],
                        "receipt": receipt,
                        "items": receipt_items,
                    }
                )
            )

        flash("บันทึกรายการรับซื้อและสร้างใบเสร็จเรียบร้อยแล้ว", "success")
        return redirect(url_for("receipt_page", purchase_id=result["purchase_id"]))

    except Exception as e:
        message = f"เกิดข้อผิดพลาดในการบันทึกรายการ: {e}"
        if is_ajax:
            return error_response(message, 500)
        flash(message, "error")
        return redirect(url_for("purchase_page"))

# ----- ai_controller.py -----

@app.route("/api/ai_status", methods=["GET"])
@login_required
def ai_status():
    return jsonify(json_ready(get_model_status_detail()))

@app.route("/api/predict_plastic", methods=["POST"])
@login_required
def predict_plastic():
    model_loaded, model_error = get_model_status()

    if not model_loaded:
        return error_response(
            "โมเดลยังไม่พร้อมใช้งาน",
            500,
            model_error,
        )

    if "image" not in request.files:
        return error_response("ไม่พบไฟล์รูปภาพ", 400)

    image_file = request.files["image"]

    if image_file.filename == "":
        return error_response("ไม่ได้เลือกรูปภาพ", 400)

    if image_file.mimetype and not image_file.mimetype.startswith("image/"):
        return error_response("กรุณาอัปโหลดไฟล์รูปภาพเท่านั้น", 400)

    try:
        response = predict_plastic_from_file(image_file)
        return jsonify(json_ready(response))

    except Exception as e:
        print("\n========== AI PREDICTION ERROR ==========")
        traceback.print_exc()
        print("=========================================\n")

        return error_response(
            "เกิดข้อผิดพลาดในการทำนาย",
            500,
            e,
        )

# ----- stock_export_controller.py -----

@app.route("/stock-export")
@login_required
def stock_export_page():
    buyers = load_stock_buyers()
    stock_items = load_exportable_stock_items()

    return render_template(
        "stock_export.html",
        current_page="stock_export",
        buyers=buyers,
        stock_items=stock_items,
    )

@app.route("/stock-export/create", methods=["POST"])
@login_required
def stock_export_create():
    try:
        result = create_stock_export_record(
            buyer_id=request.form.get("buyer_id"),
            subtype_id=request.form.get("subtype_id"),
            weight_kg=request.form.get("weight_kg"),
            unit_price=request.form.get("unit_price"),
            transport_method=request.form.get("transport_method"),
            vehicle_plate=request.form.get("vehicle_plate"),
            note=request.form.get("note"),
            created_by=session.get("user_id"),
        )

        flash(
            f"บันทึกจำหน่ายออกสำเร็จ เลขที่ {result['export_no']} "
            f"น้ำหนัก {result['weight_kg']:.2f} กก. "
            f"มูลค่า {result['amount']:.2f} บาท",
            "success",
        )

        return redirect(url_for("stock_export_history_page"))

    except Exception as e:
        flash(f"ไม่สามารถบันทึกจำหน่ายออกได้: {e}", "error")
        return redirect(url_for("stock_export_page"))

@app.route("/stock-export-history")
@login_required
def stock_export_history_page():
    keyword = request.args.get("q", "").strip()
    exports = load_stock_export_history(keyword)

    return render_template(
        "stock_export_history.html",
        current_page="stock_export_history",
        exports=exports,
        export_search=keyword,
    )

# ----- error_controller.py -----

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return error_response("ไม่พบ API ที่เรียกใช้งาน", 404)
    return "<h2>404 - ไม่พบหน้าที่ต้องการ</h2><a href='/dashboard'>กลับ Dashboard</a>", 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith("/api/"):
        return error_response("ระบบเกิดข้อผิดพลาดภายใน", 500, error)
    return "<h2>500 - ระบบเกิดข้อผิดพลาดภายใน</h2><a href='/dashboard'>กลับ Dashboard</a>", 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
