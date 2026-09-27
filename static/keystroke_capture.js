/**
 * Client-Side Keystroke Dynamics Capture (Data Minimization Mode)
 *
 * Runs entirely in the candidate's browser.
 * Computes dwell time and flight time deltas, and maps keys to high-level categories
 * ('letter', 'digit', 'backspace', 'space', 'punctuation', etc.).
 *
 * Literal keys typed and form answers are NEVER transmitted or logged.
 */

/**
 * Categorize key string into generic class client-side.
 */
function categorizeKey(key) {
  if (!key) return "other";

  if (key.length === 1) {
    if (/[a-zA-Z]/.test(key)) return "letter";
    if (/[0-9]/.test(key)) return "digit";
    if (key === " ") return "space";
    if (/^[.,!?;:'"()\[\]{}\-_\/\\@#$%^&*+=<>~`]$/.test(key)) return "punctuation";
    return "other";
  }

  const lower = key.toLowerCase();
  if (lower === "backspace") return "backspace";
  if (lower === "enter" || lower === "return") return "enter";
  if (lower === "tab") return "tab";
  if (lower === "shift" || lower === "control" || lower === "alt" || lower === "meta" || lower === "capslock") {
    return "modifier";
  }
  if (lower.startsWith("arrow")) return "arrow";
  if (lower === "delete") return "delete";
  if (lower === "escape") return "escape";
  return "other";
}

class KeystrokeCaptureClient {
  constructor(options = {}) {
    this.sessionId = options.sessionId || "default-session";
    this.apiEndpoint = options.apiEndpoint || `/api/monitoring/session/${this.sessionId}/keystroke`;
    this.batchSize = options.batchSize || 10;
    this.flushIntervalMs = options.flushIntervalMs || 3000;
    this.targetElement = options.targetElement || document;
    this.hasConsent = false;
    this.isCapturing = false;

    this.pendingKeyMap = new Map(); // key code -> { category, downTime, flight }
    this.lastKeyUpTime = null;
    this.eventBuffer = [];
    this.flushTimer = null;

    this.onBatchSent = options.onBatchSent || null;
    this.onError = options.onError || console.error;

    this._onKeyDown = this._onKeyDown.bind(this);
    this._onKeyUp = this._onKeyUp.bind(this);
  }

  setConsent(consentGiven = true) {
    this.hasConsent = Boolean(consentGiven);
  }

  _onKeyDown(e) {
    if (!this.isCapturing || !this.hasConsent) return;

    const now = Date.now();
    // NEVER store or send e.key — only derive category
    const category = categorizeKey(e.key);
    const flight = this.lastKeyUpTime ? (now - this.lastKeyUpTime) : null;

    // Use code (e.g. 'KeyA', 'Digit1') purely as internal ephemeral map key for matching keyup
    if (!this.pendingKeyMap.has(e.code)) {
      this.pendingKeyMap.set(e.code, {
        category,
        downTime: now,
        flight: flight !== null && flight >= 0 ? flight : null,
      });
    }
  }

  _onKeyUp(e) {
    if (!this.isCapturing || !this.hasConsent) return;

    const now = Date.now();
    this.lastKeyUpTime = now;

    const pending = this.pendingKeyMap.get(e.code);
    if (!pending) return;
    this.pendingKeyMap.delete(e.code);

    const dwell = Math.max(0, now - pending.downTime);

    // Derived minimal record: timing deltas and category ONLY
    const derivedEvent = {
      key_category: pending.category,
      dwell_ms: dwell,
      flight_ms: pending.flight,
      down_time: pending.downTime,
      up_time: now,
    };

    this.eventBuffer.push(derivedEvent);

    if (this.eventBuffer.length >= this.batchSize) {
      this.flush();
    }
  }

  async flush() {
    if (this.eventBuffer.length === 0) return;

    const batch = [...this.eventBuffer];
    this.eventBuffer = [];

    try {
      const response = await fetch(this.apiEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events: batch, backend: "knn" }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      if (this.onBatchSent) {
        this.onBatchSent(batch, result);
      }
    } catch (err) {
      this.onError("Failed to transmit derived keystroke batch: " + err.message);
    }
  }

  start() {
    if (!this.hasConsent) {
      throw new Error("ConsentRequiredError: Candidate consent must be confirmed before keystroke capture can start.");
    }

    if (this.isCapturing) return;
    this.isCapturing = true;

    this.targetElement.addEventListener("keydown", this._onKeyDown, true);
    this.targetElement.addEventListener("keyup", this._onKeyUp, true);

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.flushIntervalMs);
  }

  stop() {
    this.isCapturing = false;
    this.targetElement.removeEventListener("keydown", this._onKeyDown, true);
    this.targetElement.removeEventListener("keyup", this._onKeyUp, true);

    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    this.flush();
  }
}

// Attach to window
if (typeof window !== "undefined") {
  window.categorizeKey = categorizeKey;
  window.KeystrokeCaptureClient = KeystrokeCaptureClient;
}
