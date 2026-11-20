"""
Auto Journal Sync Script (v2)
==============================
Reads closed trades from MT5 terminal and writes them to Firestore so your
TradeFlow dashboard updates automatically every 5 minutes.

Setup (one-time):
1. Keep MT5 terminal OPEN and logged into your active FundedNext account.
2. Download your Firebase service account key JSON from Firebase Console >
   Project Settings > Service accounts > Generate new private key.
   Save it at: Auto Journal/keys/serviceAccountKey.json
3. Set AUTO_UID below to your Firebase user UID (sign into the journal app
   once with Google, then check your UID or email in Settings/Account).

Run:
    python sync_trades.py

The script runs forever, syncing every 5 minutes. Press Ctrl+C to stop.
"""

import MetaTrader5 as mt5
import firebase_admin
from firebase_admin import credentials, firestore
import time
from datetime import datetime, timedelta

# ==================== CONFIG ====================
# Put your Firebase UID here (from journal Settings -> Account).
AUTO_UID = "REPLACE_WITH_YOUR_FIREBASE_UID"
# How often to sync (seconds). 300 = 5 minutes.
SYNC_INTERVAL_SEC = 300
# How far back to fetch history on each run (days).
HISTORY_DAYS = 30
# =================================================

# Initialize Firebase (admin SDK - bypasses security rules)
cred = credentials.Certificate(
    "C:/Users/STR/OneDrive/Desktop/Journaling-Project/Journal/Auto Journal/keys/serviceAccountKey.json"
)
firebase_admin.initialize_app(cred)
db = firestore.client()


def init_mt5():
    if not mt5.initialize():
        print("Failed to initialize MT5. Is MetaTrader 5 open and logged in?")
        return False
    return True


def get_mt5_account_id():
    account = mt5.account_info()
    if account is None:
        print("Failed to get MT5 account info.")
        return None
    return account.login


def get_closed_trades():
    """Fetch closed (filled) trades from MT5 history."""
    trades = []
    if not init_mt5():
        return trades

    try:
        account_id = get_mt5_account_id()
        if account_id is None:
            return trades

        from_date = datetime.now() - timedelta(days=HISTORY_DAYS)
        to_date = datetime.now()

        deals = mt5.history_deals_get(from_date, to_date)
        if deals is None:
            print("MT5 returned no history (error code:", mt5.last_error(), ")")
            return trades

        for deal in deals:
            # Keep only closed deals (position fully closed / reversed)
            if deal.entry not in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY):
                continue

            trade = {
                "id": f"{account_id}-{deal.ticket}",
                "symbol": deal.symbol,
                "type": "buy" if deal.type == mt5.ORDER_TYPE_BUY else "sell",
                "volume": float(deal.volume or 0),
                "profit": float(deal.profit or 0),
                "swap": float(deal.swap or 0),
                "commission": float(deal.commission or 0),
                "time": int(deal.time),
                "account_id": account_id,
            }
            trades.append(trade)

    except Exception as e:
        print("Error fetching MT5 trades:", e)
    finally:
        mt5.shutdown()

    return trades


def map_trade_to_journal(trade):
    """Map an MT5 trade to the TradeFlow journal schema."""
    return {
        "id": trade["id"],
        "date": datetime.fromtimestamp(trade["time"]).strftime("%Y-%m-%d"),
        "type": trade["type"],
        "instrument": trade["symbol"],
        "risk": trade["volume"],        # approximate risk as lot size
        "pnl": trade["profit"],         # client sees profit (commission/swap stored separately if needed)
        "rr": "1:1",
        "emotion": "Neutral",
        "note": "",
        "chart": "",
        "ts": trade["time"] * 1000,
        "updatedAt": int(time.time() * 1000),
    }


def sync_trades():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sync started")

    trades = get_closed_trades()
    print(f"Found {len(trades)} closed MT5 trades")

    if not trades:
        print("No closed trades to sync.")
        return

    if AUTO_UID == "REPLACE_WITH_YOUR_FIREBASE_UID":
        print("ERROR: Set AUTO_UID in config before running.")
        return

    synced = 0
    for trade in trades:
        if trade["account_id"] != get_mt5_account_id():
            continue

        journal_trade = map_trade_to_journal(trade)

        doc_ref = db.collection("users").document(AUTO_UID).collection("trades").document(journal_trade["id"])
        doc_ref.set(journal_trade)
        synced += 1
        print(f"Synced: {trade['symbol']} | {trade['type']} | P&L {trade['profit']}")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Done — synced {synced} trades")


if __name__ == "__main__":
    print("Auto Journal Sync Started")
    print("Firebase UID:", AUTO_UID)
    print("Sync every", SYNC_INTERVAL_SEC // 60, "minutes")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            sync_trades()
        except KeyboardInterrupt:
            print("\nStopping sync. Goodbye!")
            break
        except Exception as e:
            print("Sync loop error:", e)

        time.sleep(SYNC_INTERVAL_SEC)
