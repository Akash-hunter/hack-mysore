/**
 * Explicit Consent Gate Component
 *
 * Renders a transparent candidate consent modal prior to proctored evaluation.
 * Prohibits telemetry capture until consent is confirmed via the backend API.
 */

class ProctoringConsentGate {
  constructor(options = {}) {
    this.sessionId = options.sessionId || "session-" + Math.random().toString(36).substring(2, 9);
    this.candidateId = options.candidateId || 1;
    this.assessmentId = options.assessmentId || 1;
    this.retentionDays = options.retentionDays || 30;
    this.onConsentGranted = options.onConsentGranted || null;
    this.onConsentDeclined = options.onConsentDeclined || null;
    this.modalElement = null;
  }

  render() {
    if (document.getElementById("proctoring-consent-modal")) return;

    const modal = document.createElement("div");
    modal.id = "proctoring-consent-modal";
    modal.className = "consent-modal-overlay";
    modal.innerHTML = `
      <div class="consent-modal-card" role="dialog" aria-modal="true" aria-labelledby="consent-title">
        <div class="consent-modal-header">
          <div class="consent-badge">DATA MINIMIZATION PROCTORING</div>
          <h2 id="consent-title">Assessment Integrity & Privacy Notice</h2>
          <p class="consent-subtitle">Please review what data is collected during your assessment session.</p>
        </div>

        <div class="consent-content-grid">
          <div class="consent-box collected-box">
            <h3><span class="icon" aria-hidden="true">&#10003;</span> What We Collect (Derived Features Only)</h3>
            <ul>
              <li><strong>Head & Gaze Landmarks:</strong> Estimated screen focus coordinates (X, Y) and confidence.</li>
              <li><strong>Typing Rhythms:</strong> Dwell time (hold duration) and flight time (latency between keys).</li>
              <li><strong>Key Categories:</strong> Generic types (e.g., 'letter', 'digit', 'backspace').</li>
              <li><strong>Browser Signals:</strong> Tab switches and copy-paste events.</li>
            </ul>
          </div>

          <div class="consent-box never-box">
            <h3><span class="icon" aria-hidden="true">&#10005;</span> What We NEVER Collect or Store</h3>
            <ul>
              <li><strong>NO Webcam Video:</strong> Camera frames are processed locally in your browser and never sent to our servers.</li>
              <li><strong>NO Audio:</strong> Microphone is never recorded or accessed.</li>
              <li><strong>NO Literal Keystrokes:</strong> We never record the actual characters or passwords you type.</li>
              <li><strong>NO Biometric Identifiers:</strong> No face prints or biometric templates are stored.</li>
            </ul>
          </div>
        </div>

        <div class="consent-retention-notice">
          <strong>Retention Policy:</strong> Granular gaze and keystroke samples are automatically shredded and permanently purged after <strong>${this.retentionDays} days</strong>.
        </div>

        <label class="consent-agreement-label">
          <input type="checkbox" id="consent-checkbox" />
          <span>I understand and consent to the collection of derived typing cadence and screen focus telemetry for assessment integrity.</span>
        </label>

        <div class="consent-actions">
          <button type="button" id="consent-decline-btn" class="consent-btn consent-btn-secondary">Decline & Exit</button>
          <button type="button" id="consent-agree-btn" class="consent-btn consent-btn-primary" disabled>I Agree & Begin Assessment</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.modalElement = modal;

    const checkbox = modal.querySelector("#consent-checkbox");
    const agreeBtn = modal.querySelector("#consent-agree-btn");
    const declineBtn = modal.querySelector("#consent-decline-btn");

    checkbox.addEventListener("change", (e) => {
      agreeBtn.disabled = !e.target.checked;
    });

    agreeBtn.addEventListener("click", () => this.submitConsent(true));
    declineBtn.addEventListener("click", () => this.handleDecline());
  }

  async submitConsent(isAgreed) {
    try {
      const response = await fetch(`/api/monitoring/session/${this.sessionId}/consent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: this.candidateId,
          assessment_id: this.assessmentId,
          consent: isAgreed,
          retention_days: this.retentionDays,
        }),
      });

      if (!response.ok) {
        throw new Error(`Consent error: HTTP ${response.status}`);
      }

      const data = await response.json();
      this.close();

      if (this.onConsentGranted) {
        this.onConsentGranted(data);
      }
    } catch (err) {
      alert("Error submitting consent: " + err.message);
    }
  }

  handleDecline() {
    this.close();
    if (this.onConsentDeclined) {
      this.onConsentDeclined();
    } else {
      window.location.href = "/";
    }
  }

  close() {
    if (this.modalElement) {
      this.modalElement.remove();
      this.modalElement = null;
    }
  }
}

// Attach to window
if (typeof window !== "undefined") {
  window.ProctoringConsentGate = ProctoringConsentGate;
}
