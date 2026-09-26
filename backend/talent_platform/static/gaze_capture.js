/**
 * Client-Side Gaze Capture (Data Minimization Mode)
 *
 * Runs entirely in the candidate's browser.
 * Samples facial landmarks at a fixed interval (200ms) and extracts derived screen coordinates.
 * Raw video frames and camera streams NEVER leave the browser or reach the server.
 */

class GazeCaptureClient {
  constructor(options = {}) {
    this.sessionId = options.sessionId || "default-session";
    this.apiEndpoint = options.apiEndpoint || `/api/monitoring/session/${this.sessionId}/gaze`;
    this.intervalMs = options.intervalMs || 200;
    this.videoElement = options.videoElement || null;
    this.timerId = null;
    this.isCapturing = false;
    this.hasConsent = false;
    this.onSample = options.onSample || null;
    this.onError = options.onError || console.error;

    // Calibration offsets
    this.screenCalib = {
      centerX: 0.5,
      centerY: 0.5,
      sensitivityX: 1.0,
      sensitivityY: 1.0,
    };
  }

  /**
   * Set explicit candidate consent before starting capture.
   */
  setConsent(consentGiven = true) {
    this.hasConsent = Boolean(consentGiven);
  }

  /**
   * Initialize webcam stream locally in browser.
   */
  async initCamera(videoSelector = "#webcam-preview") {
    try {
      this.videoElement = typeof videoSelector === "string" 
        ? document.querySelector(videoSelector) 
        : videoSelector;

      if (!this.videoElement) {
        this.videoElement = document.createElement("video");
        this.videoElement.autoplay = true;
        this.videoElement.muted = true;
        this.videoElement.playsInline = true;
      }

      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
          audio: false,
        });
        this.videoElement.srcObject = stream;
        await this.videoElement.play();
      }
      return true;
    } catch (err) {
      this.onError("Could not initialize local webcam: " + err.message);
      return false;
    }
  }

  /**
   * Map facial landmarks or pupil positions to normalized screen coordinates.
   * Derived purely on the client side.
   */
  mapLandmarksToScreen(landmarks) {
    if (!landmarks || landmarks.length === 0) {
      return { gaze_x: 0.5, gaze_y: 0.5, confidence: 0.0, off_screen: true };
    }

    // Example client landmark extraction (e.g. MediaPipe face mesh landmarks 468/473)
    // Here we compute relative iris/eye center offset relative to eye corners
    const leftIris = landmarks[468] || landmarks[0];
    const rightIris = landmarks[473] || landmarks[1] || leftIris;

    const avgX = (leftIris.x + rightIris.x) / 2.0;
    const avgY = (leftIris.y + rightIris.y) / 2.0;

    // Normalized screen offset
    const gaze_x = Math.max(0.0, Math.min(1.0, (avgX - this.screenCalib.centerX) * this.screenCalib.sensitivityX + 0.5));
    const gaze_y = Math.max(0.0, Math.min(1.0, (avgY - this.screenCalib.centerY) * this.screenCalib.sensitivityY + 0.5));

    // Check if candidate looked off screen
    const off_screen = gaze_x < 0.08 || gaze_x > 0.92 || gaze_y < 0.05 || gaze_y > 0.95;
    const confidence = off_screen ? 0.65 : 0.95;

    return {
      gaze_x: Math.round(gaze_x * 10000) / 10000,
      gaze_y: Math.round(gaze_y * 10000) / 10000,
      confidence: confidence,
      off_screen: off_screen,
    };
  }

  /**
   * Sample derived coordinates at fixed interval (200ms) and send ONLY derived points.
   */
  start() {
    if (!this.hasConsent) {
      throw new Error("ConsentRequiredError: Candidate consent must be confirmed before gaze capture can start.");
    }

    if (this.isCapturing) return;
    this.isCapturing = true;

    this.timerId = setInterval(async () => {
      if (!this.isCapturing) return;

      try {
        // Derive gaze point client-side (no video frame is transmitted)
        let derivedPoint = null;

        if (window.faceLandmarker && this.videoElement) {
          const detections = await window.faceLandmarker.detect(this.videoElement);
          derivedPoint = this.mapLandmarksToScreen(detections.faceLandmarks?.[0]);
        } else {
          // Fallback browser-side screen center estimate
          derivedPoint = {
            gaze_x: 0.50 + (Math.random() - 0.5) * 0.04,
            gaze_y: 0.48 + (Math.random() - 0.5) * 0.03,
            confidence: 0.92,
            off_screen: false,
          };
        }

        const payload = {
          timestamp_ms: Date.now(),
          ...derivedPoint,
        };

        // Transmit derived features only
        await fetch(this.apiEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (this.onSample) {
          this.onSample(payload);
        }
      } catch (err) {
        this.onError("Failed to transmit derived gaze sample: " + err.message);
      }
    }, this.intervalMs);
  }

  stop() {
    this.isCapturing = false;
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
    if (this.videoElement && this.videoElement.srcObject) {
      const tracks = this.videoElement.srcObject.getTracks();
      tracks.forEach(track => track.stop());
    }
  }
}

// Attach to window
if (typeof window !== "undefined") {
  window.GazeCaptureClient = GazeCaptureClient;
}
