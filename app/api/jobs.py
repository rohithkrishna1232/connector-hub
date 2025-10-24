from flask import request, jsonify
from app.api import api_bp
from app.models import ProcessingJob, FieldMapping, db
from datetime import datetime

@api_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """Get all processing jobs"""
    try:
        jobs = ProcessingJob.query.order_by(ProcessingJob.created_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [job.to_dict() for job in jobs]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/jobs', methods=['POST'])
def create_job():
    """Create and start a new processing job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'mapping_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate mapping exists
        mapping = FieldMapping.query.get(data['mapping_id'])
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 400
        
        job = ProcessingJob(
            name=data['name'],
            mapping_id=data['mapping_id'],
            status='pending'
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Start the job asynchronously
        from app.services.job_service import JobService
        job_service = JobService()
        job_service.start_job(job.id)
        
        return jsonify({
            'success': True,
            'data': job.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific processing job"""
    try:
        job = ProcessingJob.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': job.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job"""
    try:
        job = ProcessingJob.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        if job.status not in ['pending', 'running']:
            return jsonify({
                'success': False,
                'error': 'Job cannot be cancelled in current status'
            }), 400
        
        # Cancel the job
        from app.services.job_service import JobService
        job_service = JobService()
        result = job_service.cancel_job(job_id)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>/retry', methods=['POST'])
def retry_job(job_id):
    """Retry a failed job"""
    try:
        job = ProcessingJob.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        if job.status != 'failed':
            return jsonify({
                'success': False,
                'error': 'Only failed jobs can be retried'
            }), 400
        
        # Reset job status and retry
        job.status = 'pending'
        job.records_processed = 0
        job.records_failed = 0
        job.error_log = None
        job.started_at = None
        job.completed_at = None
        
        db.session.commit()
        
        # Start the job again
        from app.services.job_service import JobService
        job_service = JobService()
        job_service.start_job(job.id)
        
        return jsonify({
            'success': True,
            'data': job.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500