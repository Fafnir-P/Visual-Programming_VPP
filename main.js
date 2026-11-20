const { app, BrowserWindow, ipcMain, safeStorage } = require('electron');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { promisify } = require('util');
const { pathToFileURL } = require('url');
const { createLockout } = require('./lockout');

const scrypt = promisify(crypto.scrypt);

const APP_URL = pathToFileURL(path.join(__dirname, 'prototype', 'index.html')).href;
const USERNAME_PATTERN = /^[A-Za-z0-9_.-]{3,32}$/;
const MIN_PASSWORD = 8;
const MAX_PASSWORD = 256;
const MAX_KEY_LENGTH = 4096;

const lockout = createLockout();

function isAppUrl(url) {
  return typeof url === 'string' && url.split(/[?#]/)[0] === APP_URL;
}

let mainWindow = null;
let currentUser = null; // lower-case account name, or null for a guest

// ---------------------------------------------------------------------------
// Local storage (accounts and encrypted keys live in the per-user app folder)
// ---------------------------------------------------------------------------

function storePath(name) {
  return path.join(app.getPath('userData'), name);
}

function readStore(name, fallback) {
  const file = storePath(name);
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch (err) {
    if (err.code === 'ENOENT') return fallback;
    throw err;
  }
  try {
    const data = JSON.parse(text);
    if (data && Array.isArray(data.items)) return data;
  } catch (err) {
    // fall through to the corrupt-file path
  }
  // Keep the unreadable file so nothing is lost, then start clean.
  fs.renameSync(file, file + '.corrupt-' + Date.now());
  return fallback;
}

function writeStore(name, data) {
  fs.mkdirSync(app.getPath('userData'), { recursive: true });
  const file = storePath(name);
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(data), { mode: 0o600 });
  fs.renameSync(tmp, file);
}

// ---------------------------------------------------------------------------
// Accounts
// ---------------------------------------------------------------------------

async function hashPassword(password, salt) {
  return scrypt(password, salt, 64);
}

function findAccount(users, name) {
  return users.items.find((u) => u.name === name) || null;
}

async function registerAccount(username, password) {
  if (typeof username !== 'string' || !USERNAME_PATTERN.test(username)) {
    return { ok: false, error: 'Username: 3 to 32 letters, numbers, dot, dash or underscore.' };
  }
  if (typeof password !== 'string' || password.length < MIN_PASSWORD || password.length > MAX_PASSWORD) {
    return { ok: false, error: 'Password must be at least ' + MIN_PASSWORD + ' characters.' };
  }
  const name = username.toLowerCase();
  if (findAccount(readStore('accounts.json', { items: [] }), name)) {
    return { ok: false, error: 'That username is taken.' };
  }
  const salt = crypto.randomBytes(16);
  const hash = await hashPassword(password, salt);
  // Read again after the await: no other call can run between this read and the write.
  const users = readStore('accounts.json', { items: [] });
  if (findAccount(users, name)) {
    return { ok: false, error: 'That username is taken.' };
  }
  users.items.push({ name, salt: salt.toString('base64'), hash: hash.toString('base64') });
  writeStore('accounts.json', users);
  currentUser = name;
  return { ok: true, username: name };
}

async function loginAccount(username, password) {
  const fail = { ok: false, error: 'Wrong username or password.' };
  if (typeof username !== 'string' || typeof password !== 'string' || password.length > MAX_PASSWORD) {
    return fail;
  }
  const name = username.toLowerCase();
  const wait = lockout.remaining(name);
  if (wait > 0) {
    return { ok: false, error: 'Too many wrong tries. Try again in ' + Math.ceil(wait / 1000) + ' seconds.' };
  }
  const users = readStore('accounts.json', { items: [] });
  const account = findAccount(users, name);
  // Always do one hash so an unknown name takes as long as a wrong password.
  const salt = account ? Buffer.from(account.salt, 'base64') : Buffer.alloc(16);
  const hash = await hashPassword(password, salt);
  const ok = account && crypto.timingSafeEqual(hash, Buffer.from(account.hash, 'base64'));
  if (!ok) {
    lockout.fail(name);
    await new Promise((resolve) => setTimeout(resolve, 500));
    return fail;
  }
  lockout.success(name);
  currentUser = name;
  return { ok: true, username: name };
}

// ---------------------------------------------------------------------------
// API key (encrypted with the operating system's key store)
// ---------------------------------------------------------------------------

async function storeKeyFor(user, key) {
  // Encrypt first, then read and write in one synchronous step so two quick
  // saves cannot overwrite each other with stale data.
  const blob = key === '' ? '' : (await safeStorage.encryptStringAsync(key)).toString('base64');
  const secrets = readStore('secrets.json', { items: [] });
  const others = secrets.items.filter((s) => s.name !== user);
  if (blob) others.push({ name: user, blob });
  writeStore('secrets.json', { items: others });
}

// Key writes run one after another, in call order, so an older save can never
// finish after a newer one and overwrite it.
let keyQueue = Promise.resolve();
function serialized(fn) {
  const run = keyQueue.then(fn);
  keyQueue = run.catch(() => {});
  return run;
}

function saveKey(key) {
  return serialized(() => saveKeyNow(key));
}

async function saveKeyNow(key) {
  const user = currentUser;
  if (!user) return { ok: false, error: 'Not signed in.' };
  if (typeof key !== 'string' || key.length > MAX_KEY_LENGTH) {
    return { ok: false, error: 'Invalid key.' };
  }
  if (key === '') {
    await storeKeyFor(user, '');
    return { ok: true, saved: false };
  }
  if (!(await safeStorage.isAsyncEncryptionAvailable())) {
    return { ok: false, error: 'Secure storage is not available on this computer. The key was not saved.' };
  }
  await storeKeyFor(user, key);
  return { ok: true, saved: true };
}

async function loadKey() {
  const user = currentUser;
  if (!user) return { ok: false, error: 'Not signed in.' };
  const secrets = readStore('secrets.json', { items: [] });
  const entry = secrets.items.find((s) => s.name === user);
  if (!entry) return { ok: true, key: '' };
  if (!(await safeStorage.isAsyncEncryptionAvailable())) {
    return { ok: false, error: 'Secure storage is not available. The saved key cannot be read.' };
  }
  try {
    const out = await safeStorage.decryptStringAsync(Buffer.from(entry.blob, 'base64'));
    if (out.shouldReEncrypt && currentUser === user) {
      // The OS key was rotated: store the key again under the new one.
      // Skipped if a newer save replaced the entry in the meantime.
      try {
        await serialized(async () => {
          const now = readStore('secrets.json', { items: [] }).items.find((s) => s.name === user);
          if (now && now.blob === entry.blob) await storeKeyFor(user, out.result);
        });
      } catch (err) { /* keep the old copy; it is tried again on the next load */ }
    }
    return { ok: true, key: out.result };
  } catch (err) {
    return { ok: false, error: 'The saved key could not be decrypted. Enter it again.' };
  }
}

// ---------------------------------------------------------------------------
// IPC: only the app's own page may call these.
// ---------------------------------------------------------------------------

function handle(channel, fn) {
  ipcMain.handle(channel, async (event, ...args) => {
    const frame = event.senderFrame;
    const fromApp = mainWindow
      && event.sender === mainWindow.webContents
      && frame
      && !frame.parent
      && typeof frame.url === 'string'
      && isAppUrl(frame.url);
    if (!fromApp) return { ok: false, error: 'Not allowed.' };
    try {
      return await fn(...args);
    } catch (err) {
      return { ok: false, error: 'Something went wrong.' };
    }
  });
}

function registerIpc() {
  handle('auth:status', async () => ({
    ok: true,
    loggedIn: currentUser !== null,
    username: currentUser,
    canEncrypt: await safeStorage.isAsyncEncryptionAvailable()
  }));
  handle('auth:register', (u, p) => registerAccount(u, p));
  handle('auth:login', (u, p) => loginAccount(u, p));
  handle('auth:logout', () => {
    currentUser = null;
    return { ok: true };
  });
  handle('key:save', (k) => saveKey(k));
  handle('key:load', () => loadKey());
  handle('key:clear', () => saveKey(''));
}

// ---------------------------------------------------------------------------
// Window
// ---------------------------------------------------------------------------

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'Visual Programming',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  mainWindow = win;
  win.on('closed', () => {
    if (mainWindow === win) mainWindow = null;
  });

  win.loadFile(path.join(__dirname, 'prototype', 'index.html'));

  // Block navigation away from the app page.
  win.webContents.on('will-navigate', (event, url) => {
    if (!isAppUrl(url)) {
      event.preventDefault();
    }
  });

  // Block new windows.
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
}

app.whenReady().then(() => {
  registerIpc();
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  currentUser = null;
  app.quit();
});
