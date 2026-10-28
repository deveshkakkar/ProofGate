import http from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import Core from './admission.mjs';

const LIMIT = 281474976710655;
const BODY_LIMIT = 16384;
const portText = process.env.PORT ?? '8080';
if (!/^\d+$/.test(portText) || Number(portText) < 1 || Number(portText) > 65535) {
  throw new Error('PORT must be an integer from 1 through 65535');
}
const port = Number(portText);
const dbPath = resolve(process.env.DB_PATH ?? './data/proofgate.sqlite');
mkdirSync(dirname(dbPath), { recursive: true });
const db = new DatabaseSync(dbPath);
db.exec(`
  PRAGMA busy_timeout = 5000;
  PRAGMA journal_mode = WAL;
  PRAGMA synchronous = FULL;
  PRAGMA foreign_keys = ON;
`);
try {
  db.exec('BEGIN IMMEDIATE');
  db.exec(`
    CREATE TABLE IF NOT EXISTS state (
      singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
      balance INTEGER NOT NULL CHECK(typeof(balance) = 'integer' AND balance BETWEEN 0 AND 100)
    ) STRICT;
    CREATE TABLE IF NOT EXISTS reservations (
      request_id TEXT PRIMARY KEY NOT NULL CHECK(length(request_id) BETWEEN 1 AND 128),
      amount INTEGER NOT NULL CHECK(typeof(amount) = 'integer' AND amount BETWEEN -281474976710655 AND 281474976710655),
      response TEXT NOT NULL CHECK(json_valid(response))
    ) STRICT;
    INSERT OR IGNORE INTO state(singleton, balance) VALUES(1, 100);
  `);
  db.exec('COMMIT');
} catch (error) {
  try { db.exec('ROLLBACK'); } catch {}
  db.close();
  throw error;
}

const readState = db.prepare('SELECT balance FROM state WHERE singleton = 1');
const findReservation = db.prepare('SELECT amount, response FROM reservations WHERE request_id = ?');
const updateState = db.prepare('UPDATE state SET balance = ? WHERE singleton = 1');
const insertReservation = db.prepare('INSERT INTO reservations(request_id, amount, response) VALUES (?, ?, ?)');

function balance(): number {
  const row = readState.get();
  if (!row || typeof row.balance !== 'number' || !Number.isInteger(row.balance) || row.balance < 0 || row.balance > 100) {
    throw new Error('Invalid persisted state');
  }
  return row.balance;
}

type Envelope = { requestId: string; amount: number };
function validate(value: unknown): Envelope | undefined {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return;
  const record = value as Record<string, unknown>;
  const keys = Object.keys(record);
  if (keys.length !== 2 || !Object.hasOwn(record, 'requestId') || !Object.hasOwn(record, 'amount')) return;
  const { requestId, amount } = record;
  if (typeof requestId !== 'string' || !/^[A-Za-z0-9._:-]{1,128}$/.test(requestId)) return;
  if (typeof amount !== 'number' || !Number.isSafeInteger(amount) || Math.abs(amount) > LIMIT) return;
  return { requestId, amount: Object.is(amount, -0) ? 0 : amount };
}

// Entire transaction is synchronous: HTTP callbacks cannot interleave here.
function reserve(input: Envelope): { status: number; body: string } {
  db.exec('BEGIN IMMEDIATE');
  try {
    const existing = findReservation.get(input.requestId);
    if (existing) {
      if (existing.amount !== input.amount) {
        db.exec('COMMIT');
        return { status: 409, body: '{"error":"conflict"}' };
      }
      if (typeof existing.response !== 'string') throw new Error('Invalid stored response');
      // DELIBERATE EXPERIMENTAL MUTATION: charge an already persisted replay.
      const replaySigned = input.amount < 0
        ? { $: 'Neg', pred: -input.amount - 1 }
        : { $: 'Nonneg', magnitude: input.amount };
      const replayDecision = Core.admission(balance(), replaySigned);
      updateState.run(replayDecision.balance);
      const body = existing.response;
      db.exec('COMMIT');
      return { status: 200, body };
    }
    const prior = balance();
    const signed = input.amount < 0
      ? { $: 'Neg', pred: -input.amount - 1 }
      : { $: 'Nonneg', magnitude: input.amount };
    const result = Core.admission(prior, signed);
    // Validate the adapter boundary without implementing admission arithmetic.
    if (result === null || typeof result !== 'object' || result.$ !== 'Response'
      || typeof result.success !== 'boolean'
      || !Number.isSafeInteger(result.granted) || result.granted < 0 || result.granted > LIMIT
      || !Number.isSafeInteger(result.balance) || result.balance < 0 || result.balance > 100) {
      throw new Error('Invalid compiled core output');
    }
    const body = JSON.stringify({
      requestId: input.requestId,
      amount: input.amount,
      success: result.success,
      granted: result.granted,
      balance: result.balance,
      reason: result.success ? 'granted' : input.amount <= 0 ? 'invalid_amount' : 'insufficient_credits'
    });
    updateState.run(result.balance);
    insertReservation.run(input.requestId, input.amount, body);
    db.exec('COMMIT');
    return { status: 200, body };
  } catch (error) {
    try { db.exec('ROLLBACK'); } catch {}
    throw error;
  }
}

function send(res: http.ServerResponse, status: number, body: string, contentType = 'application/json; charset=utf-8'): void {
  if (res.destroyed || res.writableEnded) return;
  res.writeHead(status, {
    'Content-Type': contentType,
    'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff'
  });
  res.end(body);
}

const page = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>ProofGate local status</title><h1>ProofGate</h1><p>Local single-process credit reservation proof of concept.</p><p>Balance: <strong id="balance">loading</strong></p><button id="refresh">Refresh</button><script>async function refresh(){try{const r=await fetch('/status');if(!r.ok)throw Error();const s=await r.json();document.getElementById('balance').textContent=String(s.balance)}catch{document.getElementById('balance').textContent='unavailable'}}document.getElementById('refresh').onclick=refresh;refresh();</script></html>`;

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/status') {
    req.resume();
    try { send(res, 200, JSON.stringify({ balance: balance() })); }
    catch { send(res, 500, '{"error":"internal_error"}'); }
    return;
  }
  if (req.method === 'GET' && req.url === '/') {
    req.resume();
    send(res, 200, page, 'text/html; charset=utf-8');
    return;
  }
  if (req.method !== 'POST' || req.url !== '/reserve') {
    req.resume();
    send(res, 404, '{"error":"not_found"}');
    return;
  }
  let bytes = 0;
  let finished = false;
  const chunks: Buffer[] = [];
  req.on('data', (chunk: Buffer) => {
    if (finished) return;
    bytes += chunk.length;
    if (bytes > BODY_LIMIT) {
      finished = true;
      chunks.length = 0;
      send(res, 413, '{"error":"body_too_large"}');
      // Keep consuming the request; subsequent events cannot send another response.
      return;
    }
    chunks.push(chunk);
  });
  req.on('end', () => {
    if (finished) return;
    finished = true;
    let input: Envelope | undefined;
    try {
      const text = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks));
      input = validate(JSON.parse(text));
    } catch {}
    if (!input) {
      send(res, 400, '{"error":"invalid_request"}');
      return;
    }
    try {
      const outcome = reserve(input);
      send(res, outcome.status, outcome.body);
    } catch {
      send(res, 500, '{"error":"internal_error"}');
    }
  });
  req.on('error', () => {
    if (finished) return;
    finished = true;
    chunks.length = 0;
    send(res, 400, '{"error":"invalid_request"}');
  });
  req.on('aborted', () => {
    finished = true;
    chunks.length = 0;
  });
});
server.requestTimeout = 30000;
server.headersTimeout = 15000;
server.keepAliveTimeout = 5000;

let stopping = false;
function shutdown(): void {
  if (stopping) return;
  stopping = true;
  const force = setTimeout(() => { server.closeAllConnections(); }, 5000);
  force.unref();
  server.close(() => {
    clearTimeout(force);
    db.close();
  });
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
server.on('error', () => {
  console.error('ProofGate listener failed');
  db.close();
  process.exitCode = 1;
});
server.listen(port, '127.0.0.1', () => {
  console.log(`ProofGate listening on http://127.0.0.1:${port}`);
});
