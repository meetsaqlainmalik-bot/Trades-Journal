# Auto Journal — Setup Guide (Simple Steps)

## What this does
- Your MT5 trades auto-sync into the journal dashboard every 5 minutes.
- You do NOT manually log trades anymore. Just keep MT5 open.
- Trade close hote hi (max 5 min) dashboard pe show ho jata hai.
- Breach hua? Naya account MT5 me login karo → script naya data uthaye.
  Purana data clear karna ho to Settings > "All Clear" button dabao.

## Files
- `index.html`   → the journal app (dashboard only; Log Trade hidden)
- `scripts/sync_trades.py` → the auto-sync helper (runs on your PC)
- `keys/`        → put `serviceAccountKey.json` here (secret — don't share)

## One-time setup (10–15 min)

### Step 1 — Sign into the journal (Google)
Open `index.html`, sign in with Google. This gives you your Firebase UID.
Your UID appears in Settings > Account (or ask me to find it).

### Step 2 — Download Firebase service account key
1. Go to Firebase Console → project `trades-journal-bd3be`
2. ⚙️ Project Settings → Service accounts → Generate new private key
3. Save the downloaded JSON as `serviceAccountKey.json`
4. Put it in the `keys/` folder of this folder.

### Step 3 — Set your UID in the script
Open `scripts/sync_trades.py` and replace:
```python
AUTO_UID = "REPLACE_WITH_YOUR_FIREBASE_UID"
```
with your real UID (from step 1).

### Step 4 — Run the sync script
1. Make sure MetaTrader 5 is open and logged into your active account.
2. Open a terminal in `scripts/` and run:
   ```bash
   python sync_trades.py
   ```
3. It will sync every 5 minutes. Keep this window open (or add it to
   Task Scheduler so it auto-starts on login).

## Daily use
- Just keep MT5 open and the script running.
- Open the journal (`index.html`) anytime — dashboard shows latest trades.
- New account? Log into it in MT5; the script auto-detects the new login.
- Want a clean slate? Settings → All Clear.

## Notes
- PC band hai → sync pauses, but resumes and catches up when PC is on.
- Script uses the Firebase admin SDK (bypasses security rules), so it can
  write to your Firestore directly. Keep `serviceAccountKey.json` private.