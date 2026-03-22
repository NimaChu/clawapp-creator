const memoryStorage = new Map();

function getStorage() {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage;
    }
  } catch (error) {
    // Fall back to in-memory storage when localStorage is unavailable.
  }
  return {
    getItem(key) {
      return memoryStorage.has(key) ? memoryStorage.get(key) : null;
    },
    setItem(key, value) {
      memoryStorage.set(key, String(value));
    },
    removeItem(key) {
      memoryStorage.delete(key);
    },
  };
}

function normalizeNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function createGameStorage(namespace) {
  const storage = getStorage();
  const prefix = `clawspace:${namespace}:`;

  function getNumber(key, fallback = 0) {
    return normalizeNumber(storage.getItem(prefix + key), fallback);
  }

  function setNumber(key, value) {
    storage.setItem(prefix + key, String(normalizeNumber(value, 0)));
  }

  function updateBest(key, candidate, options = {}) {
    const fallback = normalizeNumber(options.fallback, 0);
    const mode = options.mode === 'min' ? 'min' : 'max';
    const current = getNumber(key, fallback);
    const next = normalizeNumber(candidate, fallback);
    const better = mode === 'min' ? next < current || current === fallback : next > current;

    if (better) {
      setNumber(key, next);
      return next;
    }
    return current;
  }

  function clear(key) {
    storage.removeItem(prefix + key);
  }

  return {
    getNumber,
    setNumber,
    updateBest,
    clear,
  };
}
