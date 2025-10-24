from app import db
from datetime import datetime
import json

class DataSource(db.Model):
    """Model for data sources"""
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # api, database, file, etc.
    connection_config = db.Column(db.Text)  # JSON string with connection details
    schema_info = db.Column(db.Text)  # JSON string with field information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    mappings = db.relationship('FieldMapping', foreign_keys='FieldMapping.source_id', backref='source')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'connection_config': json.loads(self.connection_config) if self.connection_config else {},
            'schema_info': json.loads(self.schema_info) if self.schema_info else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

class DataDestination(db.Model):
    """Model for data destinations"""
    __tablename__ = 'data_destinations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # api, database, file, etc.
    connection_config = db.Column(db.Text)  # JSON string with connection details
    schema_info = db.Column(db.Text)  # JSON string with field information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    mappings = db.relationship('FieldMapping', foreign_keys='FieldMapping.destination_id', backref='destination')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'connection_config': json.loads(self.connection_config) if self.connection_config else {},
            'schema_info': json.loads(self.schema_info) if self.schema_info else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

class FieldMapping(db.Model):
    """Model for field mappings between source and destination"""
    __tablename__ = 'field_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('data_destinations.id'), nullable=False)
    mapping_config = db.Column(db.Text, nullable=False)  # JSON string with field mappings
    transformation_rules = db.Column(db.Text)  # JSON string with transformation rules
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    jobs = db.relationship('ProcessingJob', backref='mapping')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'source_id': self.source_id,
            'destination_id': self.destination_id,
            'mapping_config': json.loads(self.mapping_config) if self.mapping_config else {},
            'transformation_rules': json.loads(self.transformation_rules) if self.transformation_rules else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'source_name': self.source.name if self.source else None,
            'destination_name': self.destination.name if self.destination else None
        }

class ProcessingJob(db.Model):
    """Model for data processing jobs"""
    __tablename__ = 'processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mapping_id = db.Column(db.Integer, db.ForeignKey('field_mappings.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    records_processed = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_log = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mapping_id': self.mapping_id,
            'status': self.status,
            'records_processed': self.records_processed,
            'records_failed': self.records_failed,
            'error_log': self.error_log,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat(),
            'mapping_name': self.mapping.name if self.mapping else None
        }