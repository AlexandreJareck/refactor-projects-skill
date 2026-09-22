import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.datetime_utils import utc_now


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if self._has_legacy_password():
            valid = hmac.compare_digest(
                self.password, hashlib.md5(password.encode()).hexdigest()
            )
            if valid:
                self.set_password(password)
            return valid
        return check_password_hash(self.password, password)

    def _has_legacy_password(self):
        return len(self.password) == 32 and all(
            character in "0123456789abcdef" for character in self.password.lower()
        )

    def is_admin(self):
        return self.role == "admin"
