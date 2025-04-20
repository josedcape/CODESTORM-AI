from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class User(db.Model):
    """User model for authentication and tracking workspaces."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    workspaces = relationship('Workspace', back_populates='user', cascade='all, delete-orphan')
    commands = relationship('Command', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Workspace(db.Model):
    """Workspace model for managing user's file workspaces."""
    __tablename__ = 'workspaces'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime)
    is_default = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='workspaces')
    files = relationship('File', back_populates='workspace', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Workspace {self.name} for user {self.user_id}>'


class File(db.Model):
    """File model for tracking files created in workspaces."""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(64))
    size = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    
    # Relationships
    workspace = relationship('Workspace', back_populates='files')
    
    def __repr__(self):
        return f'<File {self.name} in workspace {self.workspace_id}>'


class Command(db.Model):
    """Command model for tracking and saving command history."""
    __tablename__ = 'commands'
    
    id = db.Column(db.Integer, primary_key=True)
    instruction = db.Column(db.Text, nullable=False)
    generated_command = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text)
    status = db.Column(db.Integer)  # Exit code
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_used = db.Column(db.String(64))  # Which AI model was used
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='commands')
    
    def __repr__(self):
        return f'<Command {self.id}: {self.generated_command[:30]}... for user {self.user_id}>'