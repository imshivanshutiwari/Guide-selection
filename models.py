"""
Database models for the Guide Selection Project.
Uses Flask-SQLAlchemy with SQLite backend.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Base user model with role-based access control."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'guide', 'admin'
    department = db.Column(db.String(100), default='Computer Science')
    avatar_color = db.Column(db.String(7), default='#6C63FF')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    guide_profile = db.relationship('Guide', backref='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class Student(db.Model):
    """Student profile linked to a User."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    cgpa = db.Column(db.Float, nullable=False, default=0.0)
    _area_of_interest = db.Column('area_of_interest', db.Text, default='[]')
    sop_url = db.Column(db.String(500), default='')
    sop_score = db.Column(db.Float, default=0.0)
    enrollment_number = db.Column(db.String(20), default='')

    # Relationships
    preference = db.relationship('Preference', backref='student', uselist=False, cascade='all, delete-orphan')
    allocation = db.relationship('Allocation', backref='student', uselist=False, cascade='all, delete-orphan')

    @property
    def area_of_interest(self):
        """Returns the list of student interests safely."""
        try:
            return json.loads(self._area_of_interest) if self._area_of_interest else []
        except json.JSONDecodeError:
            return []

    @area_of_interest.setter
    def area_of_interest(self, value):
        """Sets the list of student interests."""
        self._area_of_interest = json.dumps(value)

    @property
    def priority_score(self):
        """Calculate priority score for matching algorithm."""
        score = self.cgpa * 10  # CGPA weight (max ~100)
        score += self.sop_score # Basic keyword match score

        # Early submission bonus
        if self.preference and self.preference.submitted_at:
            deadline = datetime(2026, 4, 1)
            submitted = self.preference.submitted_at
            # Strip timezone info for safe comparison
            if submitted.tzinfo is not None:
                submitted = submitted.replace(tzinfo=None)
            days_early = (deadline - submitted).days
            score += max(0, min(days_early * 0.5, 10))  # max 10 points, min 0
        return round(score, 2)

    def __repr__(self):
        return f'<Student {self.user.name} CGPA:{self.cgpa}>'


class Guide(db.Model):
    """Guide/Faculty profile linked to a User."""
    __tablename__ = 'guides'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=5)
    current_load = db.Column(db.Integer, default=0)
    _research_areas = db.Column('research_areas', db.Text, default='[]')
    bio = db.Column(db.Text, default='')
    scholar_id = db.Column(db.String(100), default='')
    publications = db.Column(db.JSON, nullable=True)
    designation = db.Column(db.String(100), default='Assistant Professor')

    # Relationships
    allocations = db.relationship('Allocation', backref='guide', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def research_areas(self):
        """Returns the list of guide research areas safely."""
        try:
            return json.loads(self._research_areas) if self._research_areas else []
        except json.JSONDecodeError:
            return []

    @research_areas.setter
    def research_areas(self, value):
        """Sets the list of guide research areas."""
        self._research_areas = json.dumps(value)

    @property
    def available_slots(self):
        """Returns the number of available slots for the guide."""
        return max(0, self.capacity - self.current_load)

    @property
    def is_full(self):
        """Checks if the guide has reached their capacity."""
        return self.current_load >= self.capacity

    def applicant_score(self, student):
        """Score a student applicant based on CGPA and interest match."""
        score = student.cgpa * 10
        # Interest area overlap
        student_interests = set(student.area_of_interest)
        guide_areas = set(self.research_areas)
        if student_interests and guide_areas:
            overlap = len(student_interests & guide_areas)
            score += overlap * 15
        return round(score, 2)

    def __repr__(self):
        return f'<Guide {self.user.name} [{self.available_slots}/{self.capacity}]>'


class Preference(db.Model):
    """Student's guide preference rankings (up to 3 choices)."""
    __tablename__ = 'preferences'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    choice_1_id = db.Column(db.Integer, db.ForeignKey('guides.id'), nullable=True)
    choice_2_id = db.Column(db.Integer, db.ForeignKey('guides.id'), nullable=True)
    choice_3_id = db.Column(db.Integer, db.ForeignKey('guides.id'), nullable=True)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    choice_1 = db.relationship('Guide', foreign_keys=[choice_1_id])
    choice_2 = db.relationship('Guide', foreign_keys=[choice_2_id])
    choice_3 = db.relationship('Guide', foreign_keys=[choice_3_id])

    @property
    def choices(self):
        """Return list of chosen guide IDs in order."""
        return [g for g in [self.choice_1_id, self.choice_2_id, self.choice_3_id] if g is not None]

    def __repr__(self):
        return f'<Preference student={self.student_id} choices={self.choices}>'


class Allocation(db.Model):
    """Final student-guide allocation result."""
    __tablename__ = 'allocations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    guide_id = db.Column(db.Integer, db.ForeignKey('guides.id'), nullable=False)
    status = db.Column(db.String(20), default='allocated')  # allocated, confirmed, rejected, waitlisted
    method = db.Column(db.String(20), default='auto')  # auto, manual, gale-shapley
    preference_rank = db.Column(db.Integer, default=0)  # which preference was matched (1,2,3 or 0=fallback)
    allocated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Allocation student={self.student_id} → guide={self.guide_id} ({self.method})>'


class Notification(db.Model):
    """In-app notification for users."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), default='info')  # info, success, warning, error
    title = db.Column(db.String(200), default='')
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def time_ago(self):
        """Return human-readable time ago string."""
        now = datetime.now(timezone.utc)
        diff = now - self.created_at
        if diff.days > 0:
            return f'{diff.days}d ago'
        hours = diff.seconds // 3600
        if hours > 0:
            return f'{hours}h ago'
        minutes = diff.seconds // 60
        if minutes > 0:
            return f'{minutes}m ago'
        return 'just now'

    def __repr__(self):
        return f'<Notification {self.type}: {self.title}>'


class AuditLog(db.Model):
    """Audit trail for all important actions."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(200), default='')
    details = db.Column(db.Text, default='')
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    actor = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by user={self.actor_id}>'
