#!/usr/bin/env python3
"""
StocksForNick Price Monitor
Checks stock prices every 5 minutes and emails users when sell conditions are triggered.

Usage:
    python3 price_monitor.py              # Run once (for cron)
    python3 price_monitor.py --loop       # Run continuously every 5 minutes
    python3 price_monitor.py --test       # Send test alert email
    python3 price_monitor.py --prices     # Just print current prices
"""

import json
import os
import sys
import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: python3 -m pip install --user --break-system-packages yfinance")
    sys.exit(1)

# ─── Setup ─────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
USERS_PATH = SCRIPT_DIR / "users.json"
STATE_PATH = SCRIPT_DIR / "state.json"
LOG_PATH = SCRIPT_DIR / "monitor.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("sfn-monitor")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_state():
    if STATE_PATH.exists():
        return load_json(STATE_PATH)
    return {"high_water_marks": {}, "alerts_sent": {}, "last_prices": {}}


def save_state(state):
    save_json(STATE_PATH, state)


# ─── Price Fetching ────────────────────────────────────

def fetch_prices(tickers):
    """Fetch current prices for all tickers using yfinance."""
    prices = {}
    try:
        data = yf.download(tickers, period="1d", interval="1m", progress=False)
        if data.empty:
            # Fallback: fetch individually
            for ticker in tickers:
                try:
                    t = yf.Ticker(ticker)
                    info = t.info
                    price = info.get("currentPrice") or info.get("regularMarketPrice")
                    if price:
                        prices[ticker] = round(float(price), 2)
                except Exception as e:
                    log.warning(f"Failed to fetch {ticker}: {e}")
        else:
            close = data["Close"]
            if hasattr(close, "columns"):
                for ticker in tickers:
                    if ticker in close.columns:
                        val = close[ticker].dropna()
                        if len(val) > 0:
                            prices[ticker] = round(float(val.iloc[-1]), 2)
            else:
                # Single ticker
                val = close.dropna()
                if len(val) > 0:
                    prices[tickers[0]] = round(float(val.iloc[-1]), 2)
    except Exception as e:
        log.error(f"Batch fetch failed: {e}")
        # Fallback individual
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                info = t.info
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                if price:
                    prices[ticker] = round(float(price), 2)
            except Exception as e2:
                log.warning(f"Individual fetch failed for {ticker}: {e2}")

    log.info(f"Fetched prices for {len(prices)}/{len(tickers)} tickers")
    return prices


# ─── Sell Signal Evaluation ────────────────────────────

def evaluate_signals(prices, sell_rules, state):
    """Check prices against sell rules and return triggered alerts."""
    alerts = []
    hwm = state.get("high_water_marks", {})

    for ticker, price in prices.items():
        if ticker not in sell_rules:
            continue

        rule = sell_rules[ticker]
        entry = rule["entry"]
        stop = rule["stop_loss"]
        target = rule["target"]
        trail_pct = rule["trailing_stop_pct"]
        partial_target = rule.get("partial_target")
        change_pct = round((price - entry) / entry * 100, 2)

        # Update high water mark
        if ticker not in hwm or price > hwm[ticker]:
            hwm[ticker] = price

        high = hwm[ticker]
        trailing_stop_price = round(high * (1 - trail_pct / 100), 2)

        # Check conditions
        if price <= stop:
            alerts.append({
                "ticker": ticker,
                "company": rule["company"],
                "category": rule["category"],
                "signal": "STOP LOSS HIT",
                "urgency": "CRITICAL",
                "price": price,
                "entry": entry,
                "trigger_price": stop,
                "change_pct": change_pct,
                "message": f"{ticker} hit stop loss at ${stop}. Current: ${price} ({change_pct:+.1f}% from entry). EXIT IMMEDIATELY.",
                "strategy": rule["strategy"]
            })
        elif price <= trailing_stop_price and price < high * 0.98:
            alerts.append({
                "ticker": ticker,
                "company": rule["company"],
                "category": rule["category"],
                "signal": "TRAILING STOP HIT",
                "urgency": "HIGH",
                "price": price,
                "entry": entry,
                "trigger_price": trailing_stop_price,
                "change_pct": change_pct,
                "message": f"{ticker} trailing stop triggered. High: ${high}, {trail_pct}% stop at ${trailing_stop_price}. Current: ${price} ({change_pct:+.1f}%). SELL.",
                "strategy": rule["strategy"]
            })
        elif price >= target:
            alerts.append({
                "ticker": ticker,
                "company": rule["company"],
                "category": rule["category"],
                "signal": "TARGET REACHED",
                "urgency": "HIGH",
                "price": price,
                "entry": entry,
                "trigger_price": target,
                "change_pct": change_pct,
                "message": f"{ticker} hit sell target ${target}! Current: ${price} ({change_pct:+.1f}%). TAKE PROFITS.",
                "strategy": rule["strategy"]
            })
        elif partial_target and price >= partial_target:
            alerts.append({
                "ticker": ticker,
                "company": rule["company"],
                "category": rule["category"],
                "signal": "PARTIAL TARGET",
                "urgency": "MEDIUM",
                "price": price,
                "entry": entry,
                "trigger_price": partial_target,
                "change_pct": change_pct,
                "message": f"{ticker} hit partial sell target ${partial_target}. Current: ${price} ({change_pct:+.1f}%). Consider trimming {rule.get('partial_pct', 33)}%.",
                "strategy": rule["strategy"]
            })

    state["high_water_marks"] = hwm
    return alerts


def filter_user_alerts(alerts, user):
    """Only alert on tickers the user has open positions in."""
    user_tickers = set()
    positions = {}
    for trade in user.get("trades", []):
        t = trade["ticker"]
        if t not in positions:
            positions[t] = 0
        if trade["action"] == "BUY":
            positions[t] += trade["shares"]
        elif trade["action"] == "SELL":
            positions[t] -= trade["shares"]

    for t, shares in positions.items():
        if shares > 0:
            user_tickers.add(t)

    # If user has no trades logged, send all alerts (they may be following along)
    if not user_tickers:
        return alerts

    return [a for a in alerts if a["ticker"] in user_tickers]


# ─── Email ─────────────────────────────────────────────

def build_alert_email(alerts, user, prices, sell_rules):
    """Build an HTML email with sell alerts."""
    name = user.get("first_name", user.get("username", "Trader"))
    now = datetime.now().strftime("%b %d, %Y %I:%M %p ET")

    # Sort by urgency
    urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    alerts.sort(key=lambda a: urgency_order.get(a["urgency"], 3))

    urgency_colors = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#f59e0b"
    }

    signal_icons = {
        "STOP LOSS HIT": "&#x1F6A8;",
        "TRAILING STOP HIT": "&#x26A0;&#xFE0F;",
        "TARGET REACHED": "&#x1F3AF;",
        "PARTIAL TARGET": "&#x1F4B0;"
    }

    alert_rows = ""
    for a in alerts:
        color = urgency_colors.get(a["urgency"], "#64748b")
        icon = signal_icons.get(a["signal"], "")
        change_color = "#10b981" if a["change_pct"] >= 0 else "#ef4444"
        change_sign = "+" if a["change_pct"] >= 0 else ""

        alert_rows += f"""
        <tr style="border-bottom:1px solid #1e293b;">
            <td style="padding:12px 8px;font-weight:700;font-size:16px;">{a['ticker']}</td>
            <td style="padding:12px 8px;">
                <span style="background:{color}22;color:{color};padding:3px 8px;border-radius:4px;font-size:12px;font-weight:700;">{icon} {a['signal']}</span>
            </td>
            <td style="padding:12px 8px;font-size:14px;">${a['price']}</td>
            <td style="padding:12px 8px;color:{change_color};font-weight:600;font-size:14px;">{change_sign}{a['change_pct']}%</td>
        </tr>
        <tr style="border-bottom:2px solid #1e293b;">
            <td colspan="4" style="padding:4px 8px 12px;color:#94a3b8;font-size:13px;">{a['message']}</td>
        </tr>"""

    # Price overview for all positions
    price_rows = ""
    for ticker in sorted(prices.keys()):
        if ticker in sell_rules:
            r = sell_rules[ticker]
            p = prices[ticker]
            chg = round((p - r["entry"]) / r["entry"] * 100, 2)
            chg_color = "#10b981" if chg >= 0 else "#ef4444"
            chg_sign = "+" if chg >= 0 else ""
            to_target = round((r["target"] - p) / p * 100, 1)
            to_stop = round((p - r["stop_loss"]) / p * 100, 1)
            price_rows += f"""
            <tr style="border-bottom:1px solid #1e293b;">
                <td style="padding:6px 8px;font-weight:600;font-size:13px;">{ticker}</td>
                <td style="padding:6px 8px;font-size:13px;">${p}</td>
                <td style="padding:6px 8px;color:{chg_color};font-weight:600;font-size:13px;">{chg_sign}{chg}%</td>
                <td style="padding:6px 8px;color:#10b981;font-size:12px;">{to_target}% to target</td>
                <td style="padding:6px 8px;color:#ef4444;font-size:12px;">{to_stop}% above stop</td>
            </tr>"""

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0b0e17;color:#f1f5f9;max-width:640px;margin:0 auto;padding:0;">
        <div style="background:linear-gradient(135deg,#1e293b,#0f172a);padding:24px;border-bottom:2px solid #ef4444;">
            <h1 style="margin:0;font-size:22px;font-weight:800;">&#x1F6A8; StocksForNick Sell Alert</h1>
            <p style="margin:6px 0 0;color:#94a3b8;font-size:14px;">{now}</p>
        </div>

        <div style="padding:20px;">
            <p style="font-size:15px;margin:0 0 16px;">Hey {name}, <strong>{len(alerts)} alert{'s' if len(alerts) != 1 else ''}</strong> triggered:</p>

            <table style="width:100%;border-collapse:collapse;background:#111827;border-radius:8px;overflow:hidden;">
                <thead>
                    <tr style="background:#1a2234;">
                        <th style="padding:10px 8px;text-align:left;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;">Ticker</th>
                        <th style="padding:10px 8px;text-align:left;font-size:11px;color:#64748b;text-transform:uppercase;">Signal</th>
                        <th style="padding:10px 8px;text-align:left;font-size:11px;color:#64748b;text-transform:uppercase;">Price</th>
                        <th style="padding:10px 8px;text-align:left;font-size:11px;color:#64748b;text-transform:uppercase;">From Entry</th>
                    </tr>
                </thead>
                <tbody>{alert_rows}</tbody>
            </table>
        </div>

        <div style="padding:0 20px 20px;">
            <h2 style="font-size:16px;font-weight:700;margin:0 0 12px;color:#94a3b8;">All Positions Overview</h2>
            <table style="width:100%;border-collapse:collapse;background:#111827;border-radius:8px;overflow:hidden;">
                <thead>
                    <tr style="background:#1a2234;">
                        <th style="padding:8px;text-align:left;font-size:11px;color:#64748b;">Ticker</th>
                        <th style="padding:8px;text-align:left;font-size:11px;color:#64748b;">Price</th>
                        <th style="padding:8px;text-align:left;font-size:11px;color:#64748b;">P&L</th>
                        <th style="padding:8px;text-align:left;font-size:11px;color:#64748b;">To Target</th>
                        <th style="padding:8px;text-align:left;font-size:11px;color:#64748b;">Above Stop</th>
                    </tr>
                </thead>
                <tbody>{price_rows}</tbody>
            </table>
        </div>

        <div style="padding:16px 20px;background:#1a2234;border-top:1px solid #1e293b;text-align:center;">
            <p style="margin:0;font-size:12px;color:#64748b;">
                StocksForNick &middot; <a href="https://stocksfornick.lewbutler.com" style="color:#3b82f6;">View Dashboard</a>
                <br>Not financial advice. Do your own research.
            </p>
        </div>
    </div>
    """
    return html


def send_email(to_email, subject, html_body, config):
    """Send email via Gmail SMTP."""
    smtp_server = config["smtp_server"]
    smtp_port = config["smtp_port"]
    sender = config["sender_email"]
    password = config["app_password"]

    if password == "REPLACE_WITH_APP_PASSWORD":
        log.error("Gmail app password not configured. See MONITOR_SETUP.md for instructions.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"StocksForNick <{sender}>"
    msg["To"] = to_email

    # Plain text fallback
    plain = f"StocksForNick Sell Alert - Check https://stocksfornick.lewbutler.com for details."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        log.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        log.error(f"Failed to send email to {to_email}: {e}")
        return False


# ─── Dedup: don't spam same alert ──────────────────────

def should_send_alert(ticker, signal, state):
    """Only send each alert type once per day per ticker."""
    key = f"{ticker}:{signal}"
    sent = state.get("alerts_sent", {})
    today = datetime.now().strftime("%Y-%m-%d")

    if key in sent and sent[key] == today:
        return False

    sent[key] = today
    state["alerts_sent"] = sent
    return True


# ─── Main ──────────────────────────────────────────────

def run_check():
    """Run one price check cycle."""
    config = load_json(CONFIG_PATH)
    users = load_json(USERS_PATH)
    state = load_state()
    sell_rules = config["sell_rules"]
    tickers = config["tickers"]

    log.info("Fetching prices...")
    prices = fetch_prices(tickers)

    if not prices:
        log.warning("No prices fetched, skipping cycle")
        return

    state["last_prices"] = prices
    state["last_check"] = datetime.now().isoformat()

    # Evaluate signals
    alerts = evaluate_signals(prices, sell_rules, state)

    if alerts:
        # Dedup
        new_alerts = [a for a in alerts if should_send_alert(a["ticker"], a["signal"], state)]

        if new_alerts:
            log.info(f"{len(new_alerts)} new alerts: {[a['ticker'] + ':' + a['signal'] for a in new_alerts]}")

            for user in users["users"]:
                user_alerts = filter_user_alerts(new_alerts, user)
                if user_alerts:
                    subject = f"StocksForNick Alert: {', '.join(a['ticker'] for a in user_alerts)} - Action Required"
                    html = build_alert_email(user_alerts, user, prices, sell_rules)
                    send_email(user["email"], subject, html, config["email"])
        else:
            log.info("Alerts already sent today, skipping")
    else:
        log.info("No alerts triggered")

    # Log price summary
    for ticker in sorted(prices.keys()):
        if ticker in sell_rules:
            r = sell_rules[ticker]
            p = prices[ticker]
            chg = round((p - r["entry"]) / r["entry"] * 100, 2)
            log.info(f"  {ticker}: ${p} ({chg:+.1f}%) | Stop: ${r['stop_loss']} | Target: ${r['target']}")

    save_state(state)


def run_test(email=None):
    """Send a test alert email."""
    config = load_json(CONFIG_PATH)
    users = load_json(USERS_PATH)
    sell_rules = config["sell_rules"]

    log.info("Fetching live prices for test email...")
    prices = fetch_prices(config["tickers"])

    if not prices:
        log.error("Could not fetch prices")
        return

    # Create sample alerts for demo
    test_alerts = [
        {
            "ticker": "PANW", "company": "Palo Alto Networks", "category": "core",
            "signal": "PARTIAL TARGET", "urgency": "MEDIUM",
            "price": prices.get("PANW", 210), "entry": 166, "trigger_price": 210,
            "change_pct": round((prices.get("PANW", 210) - 166) / 166 * 100, 2),
            "message": f"PANW hit partial sell target $210. Current: ${prices.get('PANW', 210)}. Consider trimming 33%.",
            "strategy": sell_rules["PANW"]["strategy"]
        },
        {
            "ticker": "CEG", "company": "Constellation Energy", "category": "core",
            "signal": "TARGET REACHED", "urgency": "HIGH",
            "price": prices.get("CEG", 407), "entry": 288, "trigger_price": 407,
            "change_pct": round((prices.get("CEG", 407) - 288) / 288 * 100, 2),
            "message": f"CEG hit sell target $407! Current: ${prices.get('CEG', 407)}. TAKE PROFITS.",
            "strategy": sell_rules["CEG"]["strategy"]
        }
    ]

    to = email or users["users"][0]["email"]
    subject = "[TEST] StocksForNick Sell Alert Demo"
    html = build_alert_email(test_alerts, users["users"][0], prices, sell_rules)

    log.info(f"Sending test email to {to}...")

    # Try SMTP first
    if config["email"]["app_password"] != "REPLACE_WITH_APP_PASSWORD":
        success = send_email(to, subject, html, config["email"])
        if success:
            log.info("Test email sent via SMTP!")
            return html
    else:
        log.info("SMTP not configured. Saving email HTML to test_email.html for preview.")

    # Save HTML for preview
    out_path = SCRIPT_DIR / "test_email.html"
    with open(out_path, "w") as f:
        f.write(html)
    log.info(f"Test email HTML saved to {out_path}")
    return html


def print_prices():
    """Just print current prices."""
    config = load_json(CONFIG_PATH)
    prices = fetch_prices(config["tickers"])
    sell_rules = config["sell_rules"]

    print(f"\n{'Ticker':<8} {'Price':>8} {'Change':>8} {'Stop':>8} {'Target':>8} {'Category':<10}")
    print("-" * 60)
    for ticker in sorted(prices.keys()):
        if ticker in sell_rules:
            r = sell_rules[ticker]
            p = prices[ticker]
            chg = (p - r["entry"]) / r["entry"] * 100
            print(f"{ticker:<8} ${p:>7.2f} {chg:>+7.1f}% ${r['stop_loss']:>7} ${r['target']:>7} {r['category']:<10}")


if __name__ == "__main__":
    if "--test" in sys.argv:
        email_arg = None
        for i, arg in enumerate(sys.argv):
            if arg == "--email" and i + 1 < len(sys.argv):
                email_arg = sys.argv[i + 1]
        run_test(email_arg)
    elif "--prices" in sys.argv:
        print_prices()
    elif "--loop" in sys.argv:
        log.info("Starting continuous monitoring (Ctrl+C to stop)...")
        while True:
            try:
                run_check()
            except Exception as e:
                log.error(f"Check cycle failed: {e}")
            time.sleep(300)  # 5 minutes
    else:
        run_check()
