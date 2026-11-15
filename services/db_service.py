import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Query
from config import settings
from models.schema import TransactionItem

# Tashkent timezone UTC+5
TASHKENT_TZ = timezone(timedelta(hours=5))

_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
    
    if not firebase_admin._apps:
        cred_json_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        if cred_json_str:
            cred_dict = json.loads(cred_json_str)
            cred = credentials.Certificate(cred_dict)
        elif os.path.exists(settings.firebase_service_account_path):
            cred = credentials.Certificate(settings.firebase_service_account_path)
        else:
            raise FileNotFoundError(f"Firebase credentials not found at {settings.firebase_service_account_path}")
        
        firebase_admin.initialize_app(cred)
    
    _db = firestore.client()
    return _db


def get_current_time() -> datetime:
    return datetime.now(TASHKENT_TZ)


def get_or_create_user(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str] = None) -> Dict[str, Any]:
    db = get_db()
    user_ref = db.collection("users").document(str(user_id))
    doc = user_ref.get()
    now = get_current_time()
    
    if doc.exists:
        user_ref.update({
            "last_active_at": now,
            "username": username,
            "first_name": first_name,
            "last_name": last_name
        })
        return doc.to_dict()
    else:
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "joined_at": now,
            "last_active_at": now,
            "settings": {
                "currency": "UZS",
                "notifications": True,
                "timezone": "Asia/Tashkent"
            }
        }
        user_ref.set(user_data)
        return user_data


def get_all_active_users() -> List[Dict[str, Any]]:
    db = get_db()
    users_ref = db.collection("users")
    docs = users_ref.stream()
    users = []
    for doc in docs:
        d = doc.to_dict()
        users.append(d)
    return users


def add_transaction(
    user_id: int,
    item: TransactionItem,
    raw_input: str = "",
    input_type: str = "text"
) -> str:
    db = get_db()
    now = get_current_time()
    tx_ref = db.collection("transactions").document()
    tx_data = {
        "id": tx_ref.id,
        "user_id": user_id,
        "type": item.type,
        "amount": float(item.amount),
        "currency": item.currency,
        "category": item.category,
        "description": item.description,
        "raw_input": raw_input,
        "input_type": input_type,
        "created_at": now
    }
    tx_ref.set(tx_data)
    
    # Update user's last_active_at
    db.collection("users").document(str(user_id)).update({
        "last_active_at": now
    })
    return tx_ref.id


def add_transactions_batch(
    user_id: int,
    items: List[TransactionItem],
    raw_input: str = "",
    input_type: str = "text"
) -> List[Dict[str, Any]]:
    db = get_db()
    now = get_current_time()
    batch = db.batch()
    created_list = []
    
    for item in items:
        tx_ref = db.collection("transactions").document()
        tx_data = {
            "id": tx_ref.id,
            "user_id": user_id,
            "type": item.type,
            "amount": float(item.amount),
            "currency": item.currency,
            "category": item.category,
            "description": item.description,
            "raw_input": raw_input,
            "input_type": input_type,
            "created_at": now
        }
        batch.set(tx_ref, tx_data)
        created_list.append(tx_data)
        
    batch.commit()
    
    # Update user activity
    db.collection("users").document(str(user_id)).set({
        "last_active_at": now
    }, merge=True)
    
    return created_list


def delete_last_transaction(user_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    query = (
        db.collection("transactions")
        .where("user_id", "==", user_id)
        .order_by("created_at", direction=Query.DESCENDING)
        .limit(1)
    )
    docs = list(query.stream())
    if not docs:
        return None
    
    doc = docs[0]
    data = doc.to_dict()
    doc.reference.delete()
    return data


def delete_transaction_by_id(tx_id: str, user_id: int) -> bool:
    db = get_db()
    doc_ref = db.collection("transactions").document(tx_id)
    doc = doc_ref.get()
    if doc.exists and doc.to_dict().get("user_id") == user_id:
        doc_ref.delete()
        return True
    return False


def get_transactions_period(user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        query = (
            db.collection("transactions")
            .where("user_id", "==", user_id)
            .where("created_at", ">=", start_date)
            .where("created_at", "<=", end_date)
            .order_by("created_at", direction=Query.DESCENDING)
        )
        return [doc.to_dict() for doc in query.stream()]
    except Exception as e:
        # Fallback if composite index is pending or not created yet
        docs = db.collection("transactions").where("user_id", "==", user_id).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            c_at = d.get("created_at")
            if c_at and start_date <= c_at <= end_date:
                results.append(d)
        results.sort(key=lambda x: x.get("created_at", start_date), reverse=True)
        return results


def get_today_transactions(user_id: int) -> List[Dict[str, Any]]:
    now = get_current_time()
    start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=TASHKENT_TZ)
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=TASHKENT_TZ)
    return get_transactions_period(user_id, start_of_day, end_of_day)


def get_week_transactions(user_id: int) -> List[Dict[str, Any]]:
    now = get_current_time()
    # Beginning of week (Monday) or last 7 days
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return get_transactions_period(user_id, start_of_week, now)


def get_month_transactions(user_id: int) -> List[Dict[str, Any]]:
    now = get_current_time()
    start_of_month = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=TASHKENT_TZ)
    return get_transactions_period(user_id, start_of_month, now)


def calculate_stats(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_expense = 0.0
    total_income = 0.0
    categories: Dict[str, float] = {}
    
    for tx in transactions:
        amount = float(tx.get("amount", 0))
        t_type = tx.get("type", "expense")
        cat = tx.get("category", "Boshqa")
        
        if t_type == "expense":
            total_expense += amount
            categories[cat] = categories.get(cat, 0.0) + amount
        elif t_type == "income":
            total_income += amount
            
    balance = total_income - total_expense
    
    # Sort categories by spending descending
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    top_category = sorted_categories[0][0] if sorted_categories else None
    
    return {
        "count": len(transactions),
        "total_expense": total_expense,
        "total_income": total_income,
        "balance": balance,
        "categories": sorted_categories,
        "top_category": top_category
    }
