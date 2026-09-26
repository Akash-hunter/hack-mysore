from app.extensions import db

class Search(db.Model):
    __tablename__ = 'searches'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    details = db.Column(db.JSON)
