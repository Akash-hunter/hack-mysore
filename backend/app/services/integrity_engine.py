class IntegrityEngine:
    @staticmethod
    def analyze_signals(test_session):
        # Expects test_session.integrity_signals to be a list of events:
        # e.g. [{"type": "tab_switch", "timestamp": "...", "duration": 15}]
        
        signals = getattr(test_session, "integrity_signals", None)
        if not signals:
            if hasattr(test_session, "integrity_risk_score"):
                test_session.integrity_risk_score = 0.0
            return 0.0  # No risk detected
            
        risk_score = 0.0
        
        for event in signals:
            event_type = event.get("type")
            if event_type == "tab_switch":
                # Penalize for switching tabs during test
                duration = event.get("duration", 0)
                risk_score += min(10.0, duration * 0.5) 
            elif event_type == "copy_paste":
                risk_score += 15.0
            elif event_type == "focus_lost":
                risk_score += 5.0
            elif event_type == "off_screen_gaze":
                duration = event.get("duration", 1.0)
                risk_score += min(8.0, duration * 1.5)
            elif event_type == "no_face_detected":
                risk_score += 10.0
            elif event_type == "robotic_cadence":
                risk_score += 25.0
            elif event_type == "clipboard_injection":
                risk_score += 20.0
                
        # Cap at 100
        final_score = min(100.0, round(risk_score, 1))
        if hasattr(test_session, "integrity_risk_score"):
            test_session.integrity_risk_score = final_score
        
        return final_score