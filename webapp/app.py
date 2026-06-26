"""
Flask Web Application for Intelligent Management System
Provides UI for uploading CSV files, running workflows, and viewing results
"""
import utils.session
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import pandas as pd
from queue import Queue
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import crew workflow
from crew import run_crew_workflow
import settings

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Setup logging
logger = logging.getLogger(__name__)

def get_next_test_run_number():
    """Get the next test run number by checking existing test folders"""
    output_dir = Path(settings.OUTPUT_DIR)
    test_folders = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("test_")]
    
    if not test_folders:
        return 1
    
    # Extract numbers from folder names
    numbers = []
    for folder in test_folders:
        try:
            num = int(folder.name.split("_")[1])
            numbers.append(num)
        except (IndexError, ValueError):
            continue
    
    return max(numbers) + 1 if numbers else 1

def update_settings_to_test_folder(test_folder_path):
    """Update settings to point to a specific test folder"""
    test_folder = Path(test_folder_path)
    settings.OUTPUT_DIR = test_folder
    settings.FLAGGED_SKUS = test_folder / "flagged_skus.csv"
    settings.PRICE_SCENARIOS = test_folder / "price_scenarios.csv"
    settings.CAMPAIGN_SCENARIOS = test_folder / "campaign_scenarios.csv"
    settings.LABOR_ESTIMATES = test_folder / "labor_cost_estimates.csv"
    settings.RANKED_PLAN = test_folder / "ranked_action_plan.csv"
    settings.PRODUCT_FEEDBACK = test_folder / "product_feedback.csv"
    settings.FINAL_ACTIONS = test_folder / "finalized_actions.csv"
    logger.info(f"Updated settings to use test folder: {test_folder}")

# Configure upload folder using settings
UPLOAD_FOLDER = settings.UPLOADS_DIR
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Required CSV files
REQUIRED_FILES = {
    'sales': 'get_sales.csv',
    'inventory': 'get_inventory.csv',
    'price_optimizer': 'price_optimizer.csv',
    'marketing_planner': 'marketing_planner.csv',
    'labor_simulator': 'labor_simulator.csv'
}

# Expected columns for each CSV
EXPECTED_COLUMNS = {
    'sales': ['sku_id', 'sales', 'forecast', 'plan'],
    'inventory': ['sku_id', 'inventory', 'lead_time'],
    'price_optimizer': ['sku_id', 'optimal_price', 'elasticity'],
    'marketing_planner': ['sku_id', 'channels', 'spend', 'lift'],
    'labor_simulator': ['sku_id', 'labor_hours', 'cost']
}

# Global log queue for streaming
log_queue = Queue()
workflow_status = {'running': False, 'output_dir': None}

# Custom log handler to capture logs
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

# Setup logging
def setup_logging():
    """Setup logging to capture workflow logs"""
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(logging.INFO)

setup_logging()


def validate_csv_file(file_path, file_type):
    """
    Validate CSV file format and columns
    
    Args:
        file_path: Path to CSV file
        file_type: Type of file (sales, inventory, etc.)
    
    Returns:
        tuple: (is_valid, error_message, row_count)
    """
    try:
        df = pd.read_csv(file_path)
        
        # Check if file is empty
        if len(df) == 0:
            return False, f"{file_type} file is empty", 0
        
        # Check required columns
        expected_cols = EXPECTED_COLUMNS.get(file_type, [])
        missing_cols = set(expected_cols) - set(df.columns)
        
        if missing_cols:
            return False, f"{file_type} file missing columns: {', '.join(missing_cols)}", len(df)
        
        # Check for minimum rows (at least 1)
        if len(df) < 1:
            return False, f"{file_type} file must have at least 1 row of data", len(df)
        
        return True, None, len(df)
    
    except Exception as e:
        return False, f"Error reading {file_type} file: {str(e)}", 0


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle CSV file uploads"""
    try:
        uploaded_files = {}
        validation_results = {}
        
        # Check if all required files are uploaded
        for file_key, filename in REQUIRED_FILES.items():
            if file_key not in request.files:
                return jsonify({
                    'success': False,
                    'error': f'Missing required file: {filename}'
                }), 400
            
            file = request.files[file_key]
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': f'No file selected for: {filename}'
                }), 400
            
            # Save file
            file_path = UPLOAD_FOLDER / filename
            file.save(file_path)
            
            # Validate file
            is_valid, error_msg, row_count = validate_csv_file(file_path, file_key)
            
            validation_results[file_key] = {
                'valid': is_valid,
                'error': error_msg,
                'rows': row_count,
                'filename': filename
            }
            
            if not is_valid:
                # Clean up uploaded files on validation failure
                for uploaded_file in uploaded_files.values():
                    if os.path.exists(uploaded_file):
                        os.remove(uploaded_file)
                
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'validation': validation_results
                }), 400
            
            uploaded_files[file_key] = str(file_path)
        
        # Copy files to input directory
        input_dir = Path(settings.INPUT_DIR)
        for file_key, file_path in uploaded_files.items():
            target_path = input_dir / REQUIRED_FILES[file_key]
            import shutil
            shutil.copy(file_path, target_path)
        
        return jsonify({
            'success': True,
            'message': 'All files uploaded and validated successfully',
            'validation': validation_results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500


@app.route('/run-workflow', methods=['POST'])
def run_workflow():
    """Run the CrewAI workflow"""
    global workflow_status
    
    if workflow_status['running']:
        return jsonify({
            'success': False,
            'error': 'Workflow is already running'
        }), 400
    
    try:
        data = request.json
        
        # Get threshold values with defaults
        underperf_threshold = data.get('underperf_threshold')
        max_price_change = data.get('max_price_change')
        
        # Validate thresholds
        if underperf_threshold is not None:
            try:
                underperf_threshold = float(underperf_threshold)
                if underperf_threshold <= 0 or underperf_threshold >= 1:
                    return jsonify({
                        'success': False,
                        'error': 'Underperformance threshold must be between 0 and 1 (e.g., 0.1 for 10%)'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid underperformance threshold value'
                }), 400
        
        if max_price_change is not None:
            try:
                max_price_change = float(max_price_change)
                if max_price_change <= 0 or max_price_change >= 1:
                    return jsonify({
                        'success': False,
                        'error': 'Max price change must be between 0 and 1 (e.g., 0.2 for 20%)'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid max price change value'
                }), 400
        
        # Clear log queue
        while not log_queue.empty():
            log_queue.get()
        
        # Run workflow in background thread
        def run_workflow_thread():
            global workflow_status
            workflow_status['running'] = True
            
            try:
                log_queue.put("=" * 80)
                log_queue.put("Starting Intelligent Management System Workflow")
                log_queue.put("=" * 80)
                log_queue.put(f"Underperformance threshold: {underperf_threshold or 'default (10%)'}")
                log_queue.put(f"Max price change: {max_price_change or 'default (20%)'}")
                log_queue.put("=" * 80)
                
                # Create test folder for this run
                test_num = get_next_test_run_number()
                test_folder = Path(settings.OUTPUT_DIR) / f"test_{test_num}"
                test_folder.mkdir(parents=True, exist_ok=True)
                
                log_queue.put(f"📁 Created test folder: {test_folder}")
                
                # Update settings to point to test folder
                update_settings_to_test_folder(test_folder)
                
                # Also update CHOICE_SETS which is not in the helper function
                settings.CHOICE_SETS = test_folder / "choice_sets.json"
                
                # Set the output directory for the frontend
                workflow_status['output_dir'] = str(test_folder)
                
                # Run the crew workflow
                result = run_crew_workflow(underperf_threshold, max_price_change)
                
                # Keep settings pointing to test folder for subsequent operations
                # (like report generation when approvals are submitted)
                
                log_queue.put("=" * 80)
                log_queue.put("✅ Workflow completed successfully!")
                log_queue.put("=" * 80)
                
            except Exception as e:
                log_queue.put("=" * 80)
                log_queue.put(f"❌ Workflow failed: {str(e)}")
                log_queue.put("=" * 80)
            
            finally:
                workflow_status['running'] = False
                log_queue.put("__WORKFLOW_COMPLETE__")
        
        thread = threading.Thread(target=run_workflow_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Workflow started successfully'
        })
    
    except Exception as e:
        workflow_status['running'] = False
        return jsonify({
            'success': False,
            'error': f'Failed to start workflow: {str(e)}'
        }), 500


@app.route('/stream-logs')
def stream_logs():
    """Stream logs in real-time using Server-Sent Events"""
    def generate():
        while True:
            if not log_queue.empty():
                log_entry = log_queue.get()
                yield f"data: {json.dumps({'log': log_entry})}\n\n"
            else:
                time.sleep(0.1)
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/workflow-status')
def get_workflow_status():
    """Get current workflow status"""
    return jsonify({
        'running': workflow_status['running'],
        'output_dir': workflow_status['output_dir']
    })


@app.route('/output-files')
def get_output_files():
    """Get list of output files from latest run"""
    try:
        if not workflow_status['output_dir']:
            return jsonify({
                'success': False,
                'error': 'No workflow output available'
            }), 404
        
        output_dir = Path(workflow_status['output_dir'])
        if not output_dir.exists():
            return jsonify({
                'success': False,
                'error': 'Output directory not found'
            }), 404
        
        files = []
        for file_path in output_dir.glob('*.csv'):
            files.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        for file_path in output_dir.glob('*.json'):
            files.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        for file_path in output_dir.glob('*.md'):
            files.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'files': files,
            'output_dir': str(output_dir)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get output files: {str(e)}'
        }), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Download output file"""
    try:
        if not workflow_status['output_dir']:
            return jsonify({
                'success': False,
                'error': 'No workflow output available'
            }), 404
        
        file_path = Path(workflow_status['output_dir']) / secure_filename(filename)
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to download file: {str(e)}'
        }), 500


@app.route('/preview/<filename>')
def preview_file(filename):
    """Preview output file content (CSV, JSON, MD)"""
    try:
        if not workflow_status['output_dir']:
            return jsonify({
                'success': False,
                'error': 'No workflow output available'
            }), 404
        
        file_path = Path(workflow_status['output_dir']) / secure_filename(filename)
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
            # Replace NaN with empty string for valid JSON
            df = df.fillna('')
            preview_data = {
                'columns': df.columns.tolist(),
                'rows': df.head(10).to_dict('records'),
                'total_rows': len(df)
            }
            return jsonify({
                'success': True,
                'data': preview_data
            })
        elif file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'data': data
            })
        elif file_path.suffix == '.md':
            with open(file_path, 'r') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'data': {
                    'content': content,
                    'type': 'markdown',
                    'size': len(content)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported file type for preview'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to preview file: {str(e)}'
        }), 500


@app.route('/preview-input/<filename>')
def preview_input_file(filename):
    """Preview input CSV file content"""
    try:
        file_path = Path(settings.INPUT_DIR) / secure_filename(filename)
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
            # Replace NaN with empty string for valid JSON
            df = df.fillna('')
            preview_data = {
                'columns': df.columns.tolist(),
                'rows': df.head(10).to_dict('records'),
                'total_rows': len(df)
            }
            return jsonify({
                'success': True,
                'data': preview_data
            })
        elif file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported file type for preview'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to preview file: {str(e)}'
        }), 500


@app.route('/governance-decisions')
def get_governance_decisions():
    """Get governance decisions for approval popup"""
    try:
        if not workflow_status['output_dir']:
            return jsonify({
                'success': False,
                'error': 'No workflow output available'
            }), 404
        
        governance_file = Path(workflow_status['output_dir']) / 'governance_decisions.json'
        
        if not governance_file.exists():
            return jsonify({
                'success': False,
                'error': 'Governance decisions not found. Run workflow first.'
            }), 404
        
        with open(governance_file, 'r') as f:
            decisions = json.load(f)
        
        return jsonify({
            'success': True,
            'decisions': decisions
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get governance decisions: {str(e)}'
        }), 500


@app.route('/approve-governance', methods=['POST'])
def approve_governance():
    """Handle human approval/rejection of governance decisions"""
    try:
        if not workflow_status['output_dir']:
            return jsonify({
                'success': False,
                'error': 'No workflow output available'
            }), 404
        
        data = request.json
        approvals = data.get('approvals', [])  # List of {sku_id, decision, notes}
        
        if not approvals:
            return jsonify({
                'success': False,
                'error': 'No approvals provided'
            }), 400
        
        # Generate transparency report first if it doesn't exist
        report_file = Path(workflow_status['output_dir']) / 'transparency_report.csv'
        if not report_file.exists():
            logger.info("Generating transparency report...")
            # Update settings to point to the correct test folder
            update_settings_to_test_folder(workflow_status['output_dir'])
            
            # Generate report with current governance decisions
            from crew import run_report_generation
            report_result = run_report_generation()
            if not report_file.exists():
                logger.error("Failed to generate transparency report")
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate transparency report'
                }), 500
        
        logger.info(f"Loading report from {report_file}")
        report_df = pd.read_csv(report_file)
        logger.info(f"Report loaded: {len(report_df)} rows, columns: {list(report_df.columns)}")
        
        # Ensure human decision columns exist
        if 'human_decision' not in report_df.columns:
            report_df['human_decision'] = 'pending'
        if 'human_notes' not in report_df.columns:
            report_df['human_notes'] = ''
        
        # Update human decisions
        for approval in approvals:
            sku_id = approval.get('sku_id')
            decision = approval.get('decision')  # 'approved' or 'rejected'
            notes = approval.get('notes', '')
            
            if sku_id:
                mask = report_df['sku_id'] == sku_id
                if mask.any():
                    report_df.loc[mask, 'human_decision'] = decision
                    report_df.loc[mask, 'human_notes'] = notes
        
        # Save updated report
        logger.info(f"Saving updated report with human decisions to {report_file}")
        report_df.to_csv(report_file, index=False)
        logger.info("Report saved successfully")
        
        # Create final approved actions file
        # Check which decision columns exist
        logger.info("Creating final approved actions file...")
        approved_mask = pd.Series([False] * len(report_df))
        
        if 'final_decision' in report_df.columns:
            approved_mask |= (report_df['final_decision'] == 'auto-approved')
            logger.info(f"Found {(report_df['final_decision'] == 'auto-approved').sum()} auto-approved SKUs")
        
        if 'human_decision' in report_df.columns:
            approved_mask |= (report_df['human_decision'] == 'approved')
            logger.info(f"Found {(report_df['human_decision'] == 'approved').sum()} human-approved SKUs")
        
        approved_skus = report_df[approved_mask]
        logger.info(f"Total approved SKUs: {len(approved_skus)}")
        
        final_approved_file = Path(workflow_status['output_dir']) / 'final_approved_actions.csv'
        approved_skus.to_csv(final_approved_file, index=False)
        logger.info(f"Final approved actions saved to {final_approved_file}")
        
        # Log the human approvals
        audit_log = Path(settings.LOGS_DIR) / 'audit_log.csv'
        audit_entries = []
        
        for approval in approvals:
            audit_entries.append({
                'timestamp': datetime.now().isoformat(),
                'sku_id': approval.get('sku_id'),
                'agent': 'HumanReviewer',
                'action_type': 'governance_approval',
                'decision': approval.get('decision'),
                'reason': approval.get('notes', 'Human review completed')
            })
        
        if audit_entries:
            audit_df = pd.DataFrame(audit_entries)
            if audit_log.exists():
                existing_audit = pd.read_csv(audit_log)
                audit_df = pd.concat([existing_audit, audit_df], ignore_index=True)
            audit_df.to_csv(audit_log, index=False)
        
        # Regenerate report with human decisions
        logger.info("Regenerating transparency report with human decisions...")
        # Ensure settings still point to the correct test folder
        update_settings_to_test_folder(workflow_status['output_dir'])
        
        from crew import run_report_generation
        run_report_generation()
        logger.info("Report regeneration completed")
        
        logger.info(f"Approval processing completed successfully: {len(approvals)} approvals, {len(approved_skus)} total approved")
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(approvals)} approvals',
            'total_approved': len(approved_skus),
            'final_approved_file': str(final_approved_file)
        })
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Approval processing failed: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        return jsonify({
            'success': False,
            'error': f'Failed to process approvals: {str(e)}',
            'details': error_details
        }), 500


@app.route('/generate-report', methods=['POST'])
def generate_report():
    """Generate transparency report (for when popup is closed or no manual review)"""
    try:
        if not workflow_status['output_dir']:
            return jsonify({
                'success': False,
                'error': 'No workflow output available'
            }), 404
        
        # Generate the report
        from crew import run_report_generation
        result = run_report_generation()
        
        return jsonify({
            'success': True,
            'message': 'Report generated successfully',
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate report: {str(e)}'
        }), 500


@app.route('/transparency-report')
def get_transparency_report():
    """Get the final transparency report"""
    try:
        if not workflow_status['output_dir']:
            return jsonify({
                'success': False,
                'error': 'No workflow output available'
            }), 404
        
        report_file = Path(workflow_status['output_dir']) / 'transparency_report.csv'
        summary_file = Path(workflow_status['output_dir']) / 'transparency_report_summary.json'
        markdown_file = Path(workflow_status['output_dir']) / 'transparency_report.md'
        
        if not report_file.exists():
            return jsonify({
                'success': False,
                'error': 'Transparency report not found. Run workflow first.'
            }), 404
        
        # Load report
        report_df = pd.read_csv(report_file)
        # Replace NaN with empty string for valid JSON
        report_df = report_df.fillna('')
        
        # Load summary if exists
        summary = {}
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary = json.load(f)
        
        # Load markdown report if exists
        markdown_content = None
        if markdown_file.exists():
            with open(markdown_file, 'r') as f:
                markdown_content = f.read()
        
        return jsonify({
            'success': True,
            'report': {
                'columns': report_df.columns.tolist(),
                'rows': report_df.to_dict('records'),
                'total_rows': len(report_df)
            },
            'summary': summary,
            'markdown': markdown_content
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get transparency report: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Starting Intelligent Management System Web Interface")
    print("=" * 80)
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Input folder: {settings.INPUT_DIR}")
    print(f"📁 Output folder: {settings.OUTPUT_DIR}")
    print("=" * 80)
    print(f"🌐 Open your browser and navigate to: http://{settings.FLASK_HOST}:{settings.FLASK_PORT}")
    print("=" * 80)
    
    app.run(debug=settings.FLASK_DEBUG, host=settings.FLASK_HOST, port=settings.FLASK_PORT, threaded=True)
