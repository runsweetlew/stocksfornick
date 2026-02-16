-- StocksForNick Database Schema

-- Users (optional login)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    avatar_color TEXT DEFAULT '#3b82f6',
    created_at TEXT DEFAULT (datetime('now'))
);

-- User trades (actual trades users have made)
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
    shares REAL NOT NULL,
    price REAL NOT NULL,
    trade_date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- App recommendations (the picks we make)
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('core', 'wildcard', 'alternate')),
    entry_price REAL NOT NULL,
    target_price REAL NOT NULL,
    stop_loss REAL,
    confidence INTEGER NOT NULL,
    allocation_pct REAL,
    allocation_amt REAL,
    rec_date TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Daily price snapshots for tracking performance
CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    close_price REAL NOT NULL,
    change_pct REAL,
    snapshot_date TEXT NOT NULL,
    UNIQUE(ticker, snapshot_date)
);

-- Sell signal updates (updated daily)
CREATE TABLE IF NOT EXISTS sell_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    signal TEXT NOT NULL CHECK (signal IN ('HOLD', 'TRIM', 'SELL', 'STRONG_SELL', 'SOLD')),
    sell_target REAL,
    stop_loss REAL,
    trailing_stop_pct REAL,
    partial_target REAL,
    partial_pct REAL,
    analysis TEXT NOT NULL,
    triggers TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Session tokens
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);
CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON price_snapshots(ticker, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_sell_signals_ticker ON sell_signals(ticker);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
