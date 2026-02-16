-- Seed data: Initial recommendations from Feb 15, 2026 analysis

-- Core Picks
INSERT INTO recommendations (ticker, company_name, category, entry_price, target_price, stop_loss, confidence, allocation_pct, allocation_amt, rec_date) VALUES
('PANW', 'Palo Alto Networks', 'core', 166, 224, 148, 4, 18, 90, '2026-02-15'),
('ADI', 'Analog Devices', 'core', 337, 375, 305, 4, 18, 90, '2026-02-15'),
('CEG', 'Constellation Energy', 'core', 288, 407, 255, 3, 14, 70, '2026-02-15'),
('LDOS', 'Leidos Holdings', 'core', 195, 220, 178, 4, 8, 40, '2026-02-15'),
('MDT', 'Medtronic', 'core', 101, 110, 93, 3, 10, 50, '2026-02-15'),
('DASH', 'DoorDash', 'core', 160, 276, 140, 3, 18, 90, '2026-02-15'),
('CDNS', 'Cadence Design Systems', 'core', 299, 383, 270, 3, 14, 70, '2026-02-15');

-- Wildcards
INSERT INTO recommendations (ticker, company_name, category, entry_price, target_price, stop_loss, confidence, allocation_pct, allocation_amt, rec_date) VALUES
('NBIS', 'Nebius Group', 'wildcard', 97, 160, 72, 2, NULL, NULL, '2026-02-15'),
('PLTR', 'Palantir Technologies', 'wildcard', 132, 150, 112, 2, NULL, NULL, '2026-02-15'),
('COIN', 'Coinbase Global', 'wildcard', 166, 359, 135, 2, NULL, NULL, '2026-02-15');

-- Alternates
INSERT INTO recommendations (ticker, company_name, category, entry_price, target_price, stop_loss, confidence, allocation_pct, allocation_amt, rec_date) VALUES
('WMT', 'Walmart', 'alternate', 134, 150, 122, 5, NULL, NULL, '2026-02-15'),
('BKNG', 'Booking Holdings', 'alternate', 4137, 6196, 3700, 4, NULL, NULL, '2026-02-15'),
('TOL', 'Toll Brothers', 'alternate', 167, 183, 148, 3, NULL, NULL, '2026-02-15'),
('ETSY', 'Etsy', 'alternate', 50, 63, 42, 2, NULL, NULL, '2026-02-15'),
('NEM', 'Newmont Corp', 'alternate', 126, 140, 112, 4, NULL, NULL, '2026-02-15');

-- Initial sell signals (all HOLD at launch)
INSERT INTO sell_signals (ticker, signal, sell_target, stop_loss, trailing_stop_pct, partial_target, partial_pct, analysis, triggers) VALUES
('PANW', 'HOLD', 224, 148, 8, NULL, NULL, 'Await Feb 17 AMC earnings. NGS ARR growth is the key metric - needs 25%+ YoY to sustain thesis. Platformization strategy working with 82.5% subscription mix. Stock pulled back 25% from October highs creating attractive risk/reward. CyberArk acquisition integration is the wildcard.', 'Miss on NGS ARR growth (<25%), guidance below $11.5B FY rev, CyberArk integration costs surprise to downside'),
('ADI', 'HOLD', 375, 305, 7, NULL, NULL, 'Await Feb 18 BMO earnings. Analog cycle recovery is the thesis - industrial and auto end markets bottoming. Revenue inflecting positive after inventory correction. Margin expansion story intact with 74%+ gross margins. Diversified across 125K+ customers reduces concentration risk.', 'Industrial recovery stalls, auto segment misses, inventory channel restocking slower than expected'),
('CEG', 'HOLD', 407, 255, 10, NULL, NULL, 'Highest upside in core portfolio at 50% to consensus $407. Nuclear renaissance thesis strengthened by CyrusOne data center deal. Largest US nuclear fleet (32.4 GW) positions them as THE clean energy play for AI power demand. Volatile name - use wider stops.', 'Regulatory changes on nuclear power, CyrusOne deal complications, NRC license renewal issues, natural gas price collapse reducing nuclear premium'),
('LDOS', 'HOLD', 220, 178, 7, NULL, NULL, 'Smallest position (8%) reflects DOGE contract cancellation risk. Defense IT spending resilient but government efficiency push creates uncertainty. Strong backlog provides visibility. Book-to-bill ratio is the key metric to watch.', 'DOGE-driven contract cancellations, book-to-bill drops below 1.0x, defense budget sequestration talk, margin compression from fixed-price contracts'),
('MDT', 'HOLD', 110, 93, 6, NULL, NULL, 'Steady defensive play with 9% upside. Healthcare spending resilient in uncertain macro. GLP-1 weight loss drug adoption is a headwind for surgical volumes but Medtronic''s diabetes franchise (Hugo robot) provides offset. Dividend aristocrat for downside protection.', 'Diabetes segment pressure, GLP-1 headwinds on surgical volumes accelerate, FDA regulatory delays on Hugo surgical robot'),
('DASH', 'HOLD', 276, 140, 10, 220, 33, 'Largest contrarian bet - stock down 25% creating opportunity. 73% upside to consensus $276. Delivery economics improving with DashPass membership growth. International expansion and grocery/retail categories expanding TAM. Consider trimming 1/3 at $220 (38% gain).', 'Take rate compression below 12%, grocery delivery losses widen, DashPass churn increases, international markets burn cash'),
('CDNS', 'HOLD', 383, 270, 8, NULL, NULL, 'AI chip design boom drives EDA demand. Cadence is the picks-and-shovels play on chip complexity. 28% upside to $383 consensus. Synopsys competition is real but market growing fast enough for both. Computational software (CFD/FEA) diversifies revenue.', 'AI chip design TAM revision downward, Synopsys wins major competitive deals, China export restrictions impact customer base'),
('NBIS', 'HOLD', 160, 72, 15, NULL, NULL, 'EXTREME RISK - 462% YoY revenue growth is staggering but from tiny base. Yandex spinoff with Russian governance baggage. Auditor flagged material weakness. Only bet what you can lose entirely. Feb 20 BMO earnings will make or break this one.', 'Revenue growth decelerates below 200%, auditor red flags escalate, geopolitical risk from Yandex heritage, customer concentration in AI training'),
('PLTR', 'HOLD', 150, 112, 12, NULL, NULL, 'Already reported Feb 4 - use momentum. Forward PE of 110x is nose-bleed but commercial growth (54% YoY) justifies premium for true believers. Government AI modernization is multi-year tailwind. AIP platform gaining enterprise traction.', 'Government contract delays, commercial growth slows below 30% YoY, CEO stock sales accelerate, valuation multiple compresses as rates stay high'),
('COIN', 'HOLD', 359, 135, 12, 250, 33, 'Post-earnings contrarian play. Down 61% from $420 ATH despite $11B cash fortress and profitable operations. 116% upside to $359 consensus is massive. Deribit derivatives acquisition and GENIUS Act regulatory tailwinds. Consider trimming 1/3 at $250 (50% gain).', 'Crypto winter return (BTC below $60K), regulatory reversal, trading volume collapse, Deribit integration fails'),
('WMT', 'HOLD', 150, 122, 6, NULL, NULL, 'Safest name on the list. 5/5 confidence. Walmart+ membership growth and e-commerce acceleration driving comps. Defensive positioning if macro deteriorates. Small upside (12%) but high probability of achieving target.', 'Consumer spending collapses, Walmart+ growth stalls, margin pressure from wage increases, Amazon competitive pressure intensifies'),
('BKNG', 'HOLD', 6196, 3700, 8, NULL, NULL, 'Travel recovery continues. Booking is the global leader with massive network effects. 50% upside to $6,196 consensus. Premium valuation but justified by profitability and capital return. Alternative accommodations growing faster than hotels.', 'Global recession hits travel spending, Airbnb competitive threat intensifies, European regulatory burden increases, FX headwinds from strong dollar'),
('TOL', 'HOLD', 183, 148, 8, NULL, NULL, 'Luxury homebuilder benefiting from housing shortage. Feb 17 AMC earnings. Mortgage rates stabilizing supports demand. Land bank provides multi-year visibility. Cyclical name - use stops strictly.', 'Mortgage rates spike above 8%, housing starts collapse, luxury segment demand softens, land impairments'),
('ETSY', 'HOLD', 63, 42, 10, NULL, NULL, 'Deep value play at 2/5 confidence. GMS trends need to stabilize. Turnaround story requires patience. Unique marketplace moat but execution risk is real. Small position only.', 'GMS decline accelerates, seller churn increases, Amazon Handmade competitive threat, management turnover'),
('NEM', 'HOLD', 140, 112, 8, NULL, NULL, 'World''s largest gold miner riding $5,000+ gold with 45% operating margins and record FCF. Gold thesis as inflation hedge and central bank accumulation continues. Feb 19 AMC earnings.', 'Gold price drops below $4,500, mining cost inflation, geopolitical resolution reduces safe-haven demand, operational issues at key mines');

-- Initial price snapshot (entry prices as of Feb 15, 2026)
INSERT INTO price_snapshots (ticker, close_price, change_pct, snapshot_date) VALUES
('PANW', 166, 0, '2026-02-15'),
('ADI', 337, 0, '2026-02-15'),
('CEG', 288, 0, '2026-02-15'),
('LDOS', 195, 0, '2026-02-15'),
('MDT', 101, 0, '2026-02-15'),
('DASH', 160, 0, '2026-02-15'),
('CDNS', 299, 0, '2026-02-15'),
('NBIS', 97, 0, '2026-02-15'),
('PLTR', 132, 0, '2026-02-15'),
('COIN', 166, 0, '2026-02-15'),
('WMT', 134, 0, '2026-02-15'),
('BKNG', 4137, 0, '2026-02-15'),
('TOL', 167, 0, '2026-02-15'),
('ETSY', 50, 0, '2026-02-15'),
('NEM', 126, 0, '2026-02-15');
