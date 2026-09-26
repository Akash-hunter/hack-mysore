class IntegrityEngine:
    @staticmethod
    def analyze_signals(test_session):
        # Expects test_session.integrity_signals to be a list of events:
        # e.g. [{"type": "tab_switch", "timestamp": "...", "duration": 15}]
        
        signals = test_session.integrity_signals
        if not signals:
            return 0.0 # No risk detected
            
        risk_score = 0.0
        
        for event in signals:
            if event.get('type') == 'tab_switch':
                # Penalize for switching tabs during test
                duration = event.get('duration', 0)
                risk_score += min(10.0, duration * 0.5) 
            
            elif event.get('type') == 'copy_paste':
                risk_score += 15.0
                
            elif event.get('type') == 'focus_lost':
                risk_score += 5.0
                
        # Cap at 100
        test_session.integrity_risk_score = min(100.0, risk_score)
        
        return test_session.integrity_risk_score