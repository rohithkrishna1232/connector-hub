import threading
from datetime import datetime
from app.models import ProcessingJob, FieldMapping, db
from app.services.source_service import SourceService
from app.services.destination_service import DestinationService
from app.services.transformation_service import TransformationService
import json

class JobService:
    """Service for handling processing jobs"""
    
    def __init__(self):
        self.source_service = SourceService()
        self.destination_service = DestinationService()
        self.transformation_service = TransformationService()
        self.active_jobs = {}  # Dictionary to track active job threads
    
    def start_job(self, job_id):
        """Start a processing job asynchronously"""
        try:
            job = ProcessingJob.query.get(job_id)
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            if job.status not in ['pending']:
                return {'success': False, 'error': 'Job cannot be started in current status'}
            
            # Update job status to running
            job.status = 'running'
            job.started_at = datetime.utcnow()
            db.session.commit()
            
            # Start job in a separate thread
            thread = threading.Thread(target=self._execute_job, args=(job_id,))
            thread.daemon = True
            thread.start()
            
            # Track the thread
            self.active_jobs[job_id] = thread
            
            return {'success': True, 'message': 'Job started successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_job(self, job_id):
        """Execute a processing job"""
        try:
            job = ProcessingJob.query.get(job_id)
            if not job:
                return
            
            mapping = job.mapping
            if not mapping:
                self._fail_job(job, "Mapping not found")
                return
            
            source = mapping.source
            destination = mapping.destination
            
            if not source or not destination:
                self._fail_job(job, "Source or destination not found")
                return
            
            # Get data from source
            source_result = self.source_service.get_data(source)
            if not source_result.get('success'):
                self._fail_job(job, f"Failed to get data from source: {source_result.get('error')}")
                return
            
            source_data = source_result.get('data', [])
            if not source_data:
                self._complete_job(job, 0, 0, "No data to process")
                return
            
            # Apply field mapping and transformations
            mapping_config = json.loads(mapping.mapping_config) if mapping.mapping_config else {}
            transformation_rules = json.loads(mapping.transformation_rules) if mapping.transformation_rules else {}
            
            # Process data in batches
            batch_size = 100
            total_processed = 0
            total_failed = 0
            error_messages = []
            
            if isinstance(source_data, list):
                for i in range(0, len(source_data), batch_size):
                    batch = source_data[i:i + batch_size]
                    
                    try:
                        # Apply field mapping
                        mapped_data = self._apply_field_mapping(batch, mapping_config)
                        
                        # Apply transformations
                        if transformation_rules:
                            transformed_data = self.transformation_service.transform_data(mapped_data, transformation_rules)
                        else:
                            transformed_data = mapped_data
                        
                        # Send to destination
                        dest_result = self.destination_service.send_data(destination, transformed_data)
                        
                        if dest_result.get('success'):
                            total_processed += len(batch)
                        else:
                            total_failed += len(batch)
                            error_messages.append(f"Batch {i//batch_size + 1}: {dest_result.get('error')}")
                        
                        # Update job progress
                        job.records_processed = total_processed
                        job.records_failed = total_failed
                        db.session.commit()
                        
                    except Exception as e:
                        total_failed += len(batch)
                        error_messages.append(f"Batch {i//batch_size + 1}: {str(e)}")
                        
                        # Update job progress
                        job.records_processed = total_processed
                        job.records_failed = total_failed
                        db.session.commit()
            
            else:
                # Single record
                try:
                    # Apply field mapping
                    mapped_data = self._apply_field_mapping([source_data], mapping_config)[0]
                    
                    # Apply transformations
                    if transformation_rules:
                        transformed_data = self.transformation_service.transform_data(mapped_data, transformation_rules)
                    else:
                        transformed_data = mapped_data
                    
                    # Send to destination
                    dest_result = self.destination_service.send_data(destination, transformed_data)
                    
                    if dest_result.get('success'):
                        total_processed = 1
                    else:
                        total_failed = 1
                        error_messages.append(dest_result.get('error'))
                        
                except Exception as e:
                    total_failed = 1
                    error_messages.append(str(e))
            
            # Complete the job
            if total_failed > 0:
                error_log = "; ".join(error_messages[:10])  # Limit error log size
                self._complete_job(job, total_processed, total_failed, error_log)
            else:
                self._complete_job(job, total_processed, total_failed)
            
        except Exception as e:
            job = ProcessingJob.query.get(job_id)
            if job:
                self._fail_job(job, str(e))
        
        finally:
            # Remove from active jobs
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def _apply_field_mapping(self, data, mapping_config):
        """Apply field mapping to data"""
        if not mapping_config:
            return data
        
        mapped_data = []
        
        for record in data:
            mapped_record = {}
            
            for dest_field, source_field in mapping_config.items():
                if isinstance(source_field, str):
                    # Simple field mapping
                    mapped_record[dest_field] = record.get(source_field)
                elif isinstance(source_field, dict):
                    # Complex mapping with default values, etc.
                    source_key = source_field.get('source')
                    default_value = source_field.get('default')
                    
                    if source_key in record:
                        mapped_record[dest_field] = record[source_key]
                    else:
                        mapped_record[dest_field] = default_value
                else:
                    # Keep original field if mapping is not clear
                    if dest_field in record:
                        mapped_record[dest_field] = record[dest_field]
            
            mapped_data.append(mapped_record)
        
        return mapped_data
    
    def _complete_job(self, job, processed, failed, error_log=None):
        """Mark job as completed"""
        try:
            job.status = 'completed'
            job.records_processed = processed
            job.records_failed = failed
            job.completed_at = datetime.utcnow()
            if error_log:
                job.error_log = error_log
            db.session.commit()
        except Exception as e:
            print(f"Error completing job {job.id}: {str(e)}")
    
    def _fail_job(self, job, error_message):
        """Mark job as failed"""
        try:
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
            job.error_log = error_message
            db.session.commit()
        except Exception as e:
            print(f"Error failing job {job.id}: {str(e)}")
    
    def cancel_job(self, job_id):
        """Cancel a running job"""
        try:
            job = ProcessingJob.query.get(job_id)
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            if job.status not in ['pending', 'running']:
                return {'success': False, 'error': 'Job cannot be cancelled in current status'}
            
            # Update job status
            job.status = 'cancelled'
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Note: In a real implementation, you would need to implement
            # thread cancellation mechanism to stop the running job
            
            return {'success': True, 'message': 'Job cancelled successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_job_status(self, job_id):
        """Get current status of a job"""
        try:
            job = ProcessingJob.query.get(job_id)
            if not job:
                return {'success': False, 'error': 'Job not found'}
            
            return {
                'success': True,
                'status': job.status,
                'records_processed': job.records_processed,
                'records_failed': job.records_failed,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_log': job.error_log
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}