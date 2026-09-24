from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    google_id = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    picture = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    channels = db.relationship(
        "Channel",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Channel(db.Model):
    __tablename__ = "channels"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    youtube_channel_id = db.Column(
        db.String(255),
        nullable=False
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    thumbnail = db.Column(
        db.Text,
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "youtube_channel_id",
            name="unique_user_channel"
        ),
    )

class ChannelSnapshot(db.Model):
    __tablename__ = "channel_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=False, unique=True)
    subscribers = db.Column(db.Integer, default=0, nullable=False)
    views = db.Column(db.Integer, default=0, nullable=False)
    videos = db.Column(db.Integer, default=0, nullable=False)
    checked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=True)
    kind = db.Column(db.String(50), nullable=False, default="info")
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
