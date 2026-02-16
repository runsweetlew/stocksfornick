// StocksForNick - Cloudflare Workers API
// Handles auth, trades, scoreboard, and sell signals with D1 database

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS headers for local dev
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Only handle /api routes
    if (!url.pathname.startsWith('/api/')) {
      return env.ASSETS.fetch(request);
    }

    try {
      const response = await handleAPI(url.pathname, request, env);
      // Add CORS to all API responses
      Object.entries(corsHeaders).forEach(([k, v]) => response.headers.set(k, v));
      return response;
    } catch (err) {
      return json({ error: err.message }, 500, corsHeaders);
    }
  },
};

async function handleAPI(path, request, env) {
  const method = request.method;

  // Auth routes
  if (path === '/api/auth/register' && method === 'POST') return register(request, env);
  if (path === '/api/auth/login' && method === 'POST') return login(request, env);
  if (path === '/api/auth/me' && method === 'GET') return getMe(request, env);
  if (path === '/api/auth/logout' && method === 'POST') return logout(request, env);

  // Trade routes (auth required)
  if (path === '/api/trades' && method === 'POST') return submitTrade(request, env);
  if (path === '/api/trades' && method === 'GET') return getTrades(request, env);
  if (path === '/api/trades' && method === 'DELETE') return deleteTrade(request, env);

  // Public data routes
  if (path === '/api/scoreboard' && method === 'GET') return getScoreboard(env);
  if (path === '/api/picks/performance' && method === 'GET') return getPicksPerformance(env);
  if (path === '/api/sell-signals' && method === 'GET') return getSellSignals(env);
  if (path === '/api/recommendations' && method === 'GET') return getRecommendations(env);

  // Admin routes
  if (path === '/api/admin/update-prices' && method === 'POST') return updatePrices(request, env);
  if (path === '/api/admin/update-sell-signal' && method === 'POST') return updateSellSignal(request, env);

  return json({ error: 'Not found' }, 404);
}

// ─── Helpers ────────────────────────────────────────────

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  });
}

async function hashPassword(password, salt) {
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw', encoder.encode(password), 'PBKDF2', false, ['deriveBits']
  );
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: encoder.encode(salt), iterations: 100000, hash: 'SHA-256' },
    keyMaterial, 256
  );
  return btoa(String.fromCharCode(...new Uint8Array(bits)));
}

function generateToken() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}

async function getUser(request, env) {
  const auth = request.headers.get('Authorization');
  if (!auth || !auth.startsWith('Bearer ')) return null;
  const token = auth.slice(7);
  const session = await env.DB.prepare(
    'SELECT s.user_id, u.username, u.display_name, u.avatar_color FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ? AND s.expires_at > datetime("now")'
  ).bind(token).first();
  return session || null;
}

// ─── Auth ───────────────────────────────────────────────

async function register(request, env) {
  const { username, displayName, password } = await request.json();
  if (!username || !password || !displayName) {
    return json({ error: 'Username, display name, and password are required' }, 400);
  }
  if (username.length < 3 || username.length > 20) {
    return json({ error: 'Username must be 3-20 characters' }, 400);
  }
  if (password.length < 6) {
    return json({ error: 'Password must be at least 6 characters' }, 400);
  }

  const existing = await env.DB.prepare('SELECT id FROM users WHERE username = ?').bind(username.toLowerCase()).first();
  if (existing) return json({ error: 'Username already taken' }, 409);

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#f97316', '#06b6d4', '#ec4899'];
  const color = colors[Math.floor(Math.random() * colors.length)];
  const salt = generateToken().slice(0, 16);
  const hash = await hashPassword(password, salt);

  const result = await env.DB.prepare(
    'INSERT INTO users (username, display_name, password_hash, salt, avatar_color) VALUES (?, ?, ?, ?, ?)'
  ).bind(username.toLowerCase(), displayName, hash, salt, color).run();

  const token = generateToken();
  const expires = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  await env.DB.prepare(
    'INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)'
  ).bind(token, result.meta.last_row_id, expires).run();

  return json({
    token,
    user: { id: result.meta.last_row_id, username: username.toLowerCase(), displayName, avatarColor: color }
  });
}

async function login(request, env) {
  const { username, password } = await request.json();
  if (!username || !password) return json({ error: 'Username and password required' }, 400);

  const user = await env.DB.prepare(
    'SELECT id, username, display_name, password_hash, salt, avatar_color FROM users WHERE username = ?'
  ).bind(username.toLowerCase()).first();
  if (!user) return json({ error: 'Invalid credentials' }, 401);

  const hash = await hashPassword(password, user.salt);
  if (hash !== user.password_hash) return json({ error: 'Invalid credentials' }, 401);

  const token = generateToken();
  const expires = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  await env.DB.prepare(
    'INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)'
  ).bind(token, user.id, expires).run();

  return json({
    token,
    user: { id: user.id, username: user.username, displayName: user.display_name, avatarColor: user.avatar_color }
  });
}

async function getMe(request, env) {
  const user = await getUser(request, env);
  if (!user) return json({ error: 'Not authenticated' }, 401);
  return json({ user });
}

async function logout(request, env) {
  const auth = request.headers.get('Authorization');
  if (auth && auth.startsWith('Bearer ')) {
    await env.DB.prepare('DELETE FROM sessions WHERE token = ?').bind(auth.slice(7)).run();
  }
  return json({ ok: true });
}

// ─── Trades ─────────────────────────────────────────────

async function submitTrade(request, env) {
  const user = await getUser(request, env);
  if (!user) return json({ error: 'Login required to submit trades' }, 401);

  const { ticker, action, shares, price, tradeDate, notes } = await request.json();
  if (!ticker || !action || !shares || !price || !tradeDate) {
    return json({ error: 'ticker, action, shares, price, and tradeDate are required' }, 400);
  }
  if (!['BUY', 'SELL'].includes(action)) {
    return json({ error: 'action must be BUY or SELL' }, 400);
  }

  const result = await env.DB.prepare(
    'INSERT INTO trades (user_id, ticker, action, shares, price, trade_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(user.user_id, ticker.toUpperCase(), action, shares, price, tradeDate, notes || null).run();

  return json({ id: result.meta.last_row_id, ticker: ticker.toUpperCase(), action, shares, price, tradeDate });
}

async function getTrades(request, env) {
  const user = await getUser(request, env);
  if (!user) return json({ error: 'Login required' }, 401);

  const url = new URL(request.url);
  const userId = url.searchParams.get('userId') || user.user_id;

  // Users can only see their own trades
  if (parseInt(userId) !== user.user_id) {
    return json({ error: 'Unauthorized' }, 403);
  }

  const trades = await env.DB.prepare(
    'SELECT * FROM trades WHERE user_id = ? ORDER BY trade_date DESC, created_at DESC'
  ).bind(userId).all();

  return json({ trades: trades.results });
}

async function deleteTrade(request, env) {
  const user = await getUser(request, env);
  if (!user) return json({ error: 'Login required' }, 401);

  const { id } = await request.json();
  await env.DB.prepare('DELETE FROM trades WHERE id = ? AND user_id = ?').bind(id, user.user_id).run();
  return json({ ok: true });
}

// ─── Scoreboard ─────────────────────────────────────────

async function getScoreboard(env) {
  // Get all users with their trade performance
  const users = await env.DB.prepare(`
    SELECT u.id, u.display_name, u.avatar_color, u.created_at,
           COUNT(t.id) as trade_count,
           COUNT(DISTINCT t.ticker) as tickers_traded
    FROM users u
    LEFT JOIN trades t ON u.id = t.user_id
    GROUP BY u.id
    ORDER BY trade_count DESC
  `).all();

  // Get latest prices for P&L calculation
  const latestPrices = await env.DB.prepare(`
    SELECT ticker, close_price, snapshot_date
    FROM price_snapshots
    WHERE (ticker, snapshot_date) IN (
      SELECT ticker, MAX(snapshot_date) FROM price_snapshots GROUP BY ticker
    )
  `).all();

  const priceMap = {};
  for (const p of latestPrices.results) {
    priceMap[p.ticker] = p.close_price;
  }

  // Calculate P&L for each user
  const leaderboard = [];
  for (const user of users.results) {
    const trades = await env.DB.prepare(
      'SELECT * FROM trades WHERE user_id = ? ORDER BY trade_date'
    ).bind(user.id).all();

    let totalInvested = 0;
    let totalValue = 0;
    const positions = {};

    for (const t of trades.results) {
      if (t.action === 'BUY') {
        if (!positions[t.ticker]) positions[t.ticker] = { shares: 0, cost: 0 };
        positions[t.ticker].shares += t.shares;
        positions[t.ticker].cost += t.shares * t.price;
        totalInvested += t.shares * t.price;
      } else {
        if (positions[t.ticker]) {
          const avgCost = positions[t.ticker].cost / positions[t.ticker].shares;
          positions[t.ticker].shares -= t.shares;
          positions[t.ticker].cost -= t.shares * avgCost;
          totalInvested -= t.shares * avgCost;
        }
      }
    }

    // Mark-to-market
    for (const [ticker, pos] of Object.entries(positions)) {
      if (pos.shares > 0 && priceMap[ticker]) {
        totalValue += pos.shares * priceMap[ticker];
      }
    }

    const pnl = totalInvested > 0 ? ((totalValue - totalInvested) / totalInvested * 100) : 0;

    leaderboard.push({
      id: user.id,
      displayName: user.display_name,
      avatarColor: user.avatar_color,
      tradeCount: user.trade_count,
      tickersTraded: user.tickers_traded,
      totalInvested: Math.round(totalInvested * 100) / 100,
      totalValue: Math.round(totalValue * 100) / 100,
      pnlPct: Math.round(pnl * 100) / 100,
      memberSince: user.created_at,
    });
  }

  leaderboard.sort((a, b) => b.pnlPct - a.pnlPct);
  return json({ leaderboard });
}

// ─── Picks Performance ──────────────────────────────────

async function getPicksPerformance(env) {
  const recs = await env.DB.prepare(
    'SELECT * FROM recommendations ORDER BY category, ticker'
  ).all();

  const latestPrices = await env.DB.prepare(`
    SELECT ticker, close_price, snapshot_date
    FROM price_snapshots
    WHERE (ticker, snapshot_date) IN (
      SELECT ticker, MAX(snapshot_date) FROM price_snapshots GROUP BY ticker
    )
  `).all();

  const priceMap = {};
  for (const p of latestPrices.results) {
    priceMap[p.ticker] = { price: p.close_price, date: p.snapshot_date };
  }

  const performance = recs.results.map(rec => {
    const current = priceMap[rec.ticker];
    const currentPrice = current ? current.price : rec.entry_price;
    const changePct = ((currentPrice - rec.entry_price) / rec.entry_price * 100);
    const toTargetPct = ((rec.target_price - currentPrice) / currentPrice * 100);

    return {
      ticker: rec.ticker,
      company: rec.company_name,
      category: rec.category,
      entryPrice: rec.entry_price,
      currentPrice,
      targetPrice: rec.target_price,
      stopLoss: rec.stop_loss,
      confidence: rec.confidence,
      changePct: Math.round(changePct * 100) / 100,
      toTargetPct: Math.round(toTargetPct * 100) / 100,
      allocationPct: rec.allocation_pct,
      allocationAmt: rec.allocation_amt,
      lastUpdated: current ? current.date : rec.rec_date,
    };
  });

  // Portfolio weighted return (core picks only)
  const corePicks = performance.filter(p => p.category === 'core');
  const portfolioReturn = corePicks.reduce((sum, p) => {
    return sum + (p.changePct * (p.allocationPct || 0) / 100);
  }, 0);

  return json({
    performance,
    portfolioReturn: Math.round(portfolioReturn * 100) / 100,
    lastUpdated: new Date().toISOString(),
  });
}

// ─── Sell Signals ───────────────────────────────────────

async function getSellSignals(env) {
  const signals = await env.DB.prepare(`
    SELECT ss.*, r.company_name, r.category, r.entry_price, r.target_price, r.confidence
    FROM sell_signals ss
    JOIN recommendations r ON ss.ticker = r.ticker
    WHERE ss.id IN (SELECT MAX(id) FROM sell_signals GROUP BY ticker)
    ORDER BY r.category, ss.ticker
  `).all();

  return json({ signals: signals.results });
}

// ─── Recommendations ────────────────────────────────────

async function getRecommendations(env) {
  const recs = await env.DB.prepare('SELECT * FROM recommendations ORDER BY category, ticker').all();
  return json({ recommendations: recs.results });
}

// ─── Admin ──────────────────────────────────────────────

async function updatePrices(request, env) {
  const { prices } = await request.json();
  // prices: [{ ticker, price, changePct }]
  const date = new Date().toISOString().split('T')[0];

  for (const p of prices) {
    await env.DB.prepare(
      'INSERT OR REPLACE INTO price_snapshots (ticker, close_price, change_pct, snapshot_date) VALUES (?, ?, ?, ?)'
    ).bind(p.ticker, p.price, p.changePct || 0, date).run();
  }

  return json({ ok: true, updated: prices.length });
}

async function updateSellSignal(request, env) {
  const { ticker, signal, sellTarget, stopLoss, trailingStopPct, partialTarget, partialPct, analysis, triggers } = await request.json();

  await env.DB.prepare(`
    INSERT INTO sell_signals (ticker, signal, sell_target, stop_loss, trailing_stop_pct, partial_target, partial_pct, analysis, triggers)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(ticker, signal, sellTarget, stopLoss, trailingStopPct, partialTarget, partialPct, analysis, triggers).run();

  return json({ ok: true });
}
