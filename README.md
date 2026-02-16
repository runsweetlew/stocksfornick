# StocksForNick

Weekly Earnings Intelligence Dashboard with Performance Tracking, User Trade Logging, and Sell Recommendations.

**Week of February 17-22, 2026** | 7 Core Picks + 3 Wildcards + 5 Alternates | $500 Allocation

---

## Getting Started

### View the Site (No Login Required)

The site is fully viewable without an account. Browse all picks, analysis, charts, sell signals, and the public scoreboard.

**Option A - Open directly:**
```bash
open public/index.html
```

**Option B - Local server:**
```bash
python3 -m http.server 8080 --directory public
# Visit http://localhost:8080
```

**Option C - Deploy to Cloudflare (full features):**
```bash
npm install
npx wrangler d1 create stocksfornick-db
# Update database_id in wrangler.toml with the ID from above
npm run db:init:remote
npm run seed:remote
npm run deploy
```

---

## User Login (Optional)

Logging in is **completely optional**. You only need an account if you want to:
- Log trades you've actually made
- Track your personal performance
- Appear on the leaderboard

### How to Create an Account

1. Click the **"Login"** button in the top-right corner of the navigation bar
2. Click **"Create Account"** at the bottom of the login form
3. Fill in:
   - **Username** (3-20 characters, must be unique)
   - **Display Name** (shown on the leaderboard)
   - **Password** (minimum 6 characters)
4. Click **"Create Account"**
5. You're automatically logged in

### How to Login

1. Click **"Login"** in the nav bar
2. Enter your username and password
3. Click **"Sign In"**

### Logging Out

Click your avatar/name in the nav bar, then click **"Logout"**.

> **Note:** When running as a static file (not deployed to Cloudflare), accounts are stored in your browser's localStorage. Data won't sync across devices. Deploy to Cloudflare Workers for multi-device, multi-user support with the D1 database.

---

## Submitting Trades

After logging in, you can record real trades you've made:

1. Click the **"Log Trade"** button (appears after login) or use the trade panel in the Scoreboard section
2. Fill in:
   - **Ticker** - Select from the recommended stocks or type any ticker
   - **Action** - BUY or SELL
   - **Shares** - Number of shares
   - **Price** - Price per share at execution
   - **Date** - When you made the trade
   - **Notes** (optional) - Any context about the trade
3. Click **"Submit Trade"**

Your trades are used to calculate your personal P&L and rank you on the leaderboard.

---

## Scoreboard

The scoreboard tracks two things:

### 1. App Picks Performance
How the site's recommendations are performing since the Feb 15, 2026 picks:
- Entry price vs. current price for all 15 stocks
- Weighted portfolio return for the 7 core picks
- Individual stock gains/losses with color coding
- Progress toward target prices

### 2. User Leaderboard
Compare how users who logged trades are performing:
- Ranked by portfolio return (%)
- Shows total invested, current value, and P&L
- Number of trades and tickers traded
- Fun rankings with trophy/medal icons

---

## Sell Recommendations

Every pick includes detailed sell analysis:

- **Signal Status**: HOLD / TRIM / SELL / STRONG SELL
- **Sell Target**: Price to take full profits
- **Stop Loss**: Downside protection level
- **Trailing Stop**: Percentage-based stop from highs
- **Partial Target**: Price to trim position (if applicable)
- **Analysis**: Detailed reasoning updated daily
- **Sell Triggers**: Specific conditions that would change the signal

### Daily Updates

Sell signals can be updated daily based on:
- Price action and technical levels
- Earnings results
- News and fundamental changes
- Macro environment shifts

To update sell signals (admin):
```bash
curl -X POST https://your-site.com/api/admin/update-sell-signal \
  -H "Content-Type: application/json" \
  -d '{"ticker":"PANW","signal":"TRIM","analysis":"Beat earnings, trim 1/3 at $220..."}'
```

---

## Development

```bash
npm install
npm run dev          # Start local dev server with Wrangler
npm run db:init      # Initialize local D1 database
npm run seed         # Seed with initial recommendations + sell signals
```

## Deployment

```bash
# Create D1 database
npx wrangler d1 create stocksfornick-db
# Copy the database_id into wrangler.toml

# Initialize and seed remote database
npm run db:init:remote
npm run seed:remote

# Deploy
npm run deploy
```

---

## Tech Stack

- **Frontend**: HTML5 + CSS3 + Vanilla JS + Chart.js
- **Backend**: Cloudflare Workers
- **Database**: Cloudflare D1 (SQLite)
- **Auth**: PBKDF2 password hashing + session tokens
- **Deployment**: Cloudflare Pages/Workers

---

*Not financial advice. Do your own research. All investments carry risk.*
