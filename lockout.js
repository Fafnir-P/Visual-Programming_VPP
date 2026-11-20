// Login lockout, in memory only (reset when the app restarts).
// 5 wrong tries for one name -> refuse that name for 30 s; each next lockout doubles (max 10 min).
// shortcut: per name, not per computer; a restart clears it. Upgrade if accounts ever leave this machine.

function createLockout(now = Date.now, maxFails = 5, baseMs = 30000, capMs = 600000, maxNames = 1000) {
  const entries = new Map(); // name -> { fails, level, until }
  return {
    // Milliseconds left in the lockout for this name (0 = may try).
    remaining(name) {
      const e = entries.get(name);
      return e && e.until > now() ? e.until - now() : 0;
    },
    fail(name) {
      let e = entries.get(name);
      if (!e) {
        if (entries.size >= maxNames) entries.delete(entries.keys().next().value);
        e = { fails: 0, level: 0, until: 0 };
        entries.set(name, e);
      }
      e.fails += 1;
      if (e.fails >= maxFails) {
        e.until = now() + Math.min(baseMs * 2 ** e.level, capMs);
        e.level += 1;
        e.fails = 0;
      }
    },
    success(name) {
      entries.delete(name);
    }
  };
}

module.exports = { createLockout };
