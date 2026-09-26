class RankingEngine:
    @staticmethod
    def rank_candidates(applications):
        # A simple ranking by match_score descending
        # Real-world would involve weights, recruiter preferences, and AI scoring
        
        ranked = sorted(applications, key=lambda a: (a.match_score or 0), reverse=True)
        
        # Update ranking positions
        for i, app in enumerate(ranked):
            app.ranking_position = i + 1
            
        return ranked