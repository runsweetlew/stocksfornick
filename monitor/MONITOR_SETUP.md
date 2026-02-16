# StocksForNick Price Monitor Setup

Monitors stock prices every 5 minutes and emails users when sell conditions are triggered.

## What It Does

1. Fetches live prices for all 15 stocks via Yahoo Finance
2. Compares against sell rules: stop losses, trailing stops, targets, partial targets
3. Emails users with open positions when conditions trigger
4. Deduplicates alerts (one per ticker per signal per day)
5. Logs all activity to `monitor.log`

## Alert Types

| Signal | Urgency | Meaning |
|--------|---------|---------|
| STOP LOSS HIT | CRITICAL | Price dropped to stop loss. Exit immediately. |
| TRAILING STOP HIT | HIGH | Price fell X% from high water mark. Sell. |
| TARGET REACHED | HIGH | Price hit sell target. Take profits. |
| PARTIAL TARGET | MEDIUM | Price hit partial trim level. Consider selling 1/3. |

## Quick Start

### 1. Set Up Gmail App Password

You need a Google App Password for the monitor to send emails.

1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. Select "Mail" as the app, "Other" as the device (name it "StocksForNick")
4. Click "Generate"
5. Copy the 16-character password

### 2. Configure

Edit `config.json` and replace the app password:

```json
"email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "lewis@lewisbutler.com",
    "app_password": "xxxx xxxx xxxx xxxx"
}
```

### 3. Add Users

Edit `users.json` to add users and their trades:

```json
{
  "users": [
    {
      "id": 1,
      "first_name": "Lewis",
      "last_name": "Butler",
      "email": "lewis@lewisbutler.com",
      "username": "lewisbutler",
      "trades": [
        {"ticker": "PANW", "action": "BUY", "shares": 0.54, "price": 166, "date": "2026-02-17"},
        {"ticker": "CEG", "action": "BUY", "shares": 0.24, "price": 288, "date": "2026-02-17"}
      ]
    },
    {
      "id": 2,
      "first_name": "Nick",
      "last_name": "B",
      "email": "nick@example.com",
      "username": "nick",
      "trades": [
        {"ticker": "PANW", "action": "BUY", "shares": 0.54, "price": 166, "date": "2026-02-17"}
      ]
    }
  ]
}
```

**Note:** If a user has no trades listed, they'll receive ALL alerts (useful for following along without trading).

### 4. Test

```bash
# Check current prices
python3 ~/stocksfornick/monitor/price_monitor.py --prices

# Send test alert email
python3 ~/stocksfornick/monitor/price_monitor.py --test

# Run one check cycle
python3 ~/stocksfornick/monitor/price_monitor.py
```

### 5. Set Up Cron (Every 5 Minutes During Market Hours)

```bash
crontab -e
```

Add this line:
```
*/5 9-16 * * 1-5 python3 /home/lewis/stocksfornick/monitor/price_monitor.py >> /home/lewis/stocksfornick/monitor/cron.log 2>&1
```

This runs every 5 minutes, 9 AM to 4 PM, Monday through Friday.

### 6. Verify

```bash
# Check the log
tail -f ~/stocksfornick/monitor/monitor.log

# Check cron is running
grep stocksfornick /var/log/syslog 2>/dev/null || crontab -l | grep stocksfornick
```

## File Reference

| File | Purpose |
|------|---------|
| `price_monitor.py` | Main monitoring script |
| `config.json` | Sell rules, tickers, email config |
| `users.json` | Registered users and their trades |
| `state.json` | Auto-generated: high water marks, sent alerts |
| `monitor.log` | Activity log |
| `test_email.html` | Preview of last test email |

## Commands

```bash
python3 price_monitor.py              # Run one check cycle
python3 price_monitor.py --loop       # Run continuously (every 5 min)
python3 price_monitor.py --test       # Send test alert email
python3 price_monitor.py --prices     # Print current prices table
```

## Modifying Sell Rules

Edit `config.json` > `sell_rules` > `{TICKER}`:

```json
"PANW": {
    "entry": 166,
    "stop_loss": 148,
    "target": 224,
    "trailing_stop_pct": 8,
    "partial_target": 210,
    "partial_pct": 33,
    "strategy": "Hold through earnings. Take 1/3 at $210..."
}
```

Restart cron or the loop after changes.
