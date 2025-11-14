"""
Flask Web Application for Intelligent Management System
Provides UI for uploading CSV files, running workflows, and viewing results
"""
import os
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

# Import crew workflow
from crew import run_crew_workflow
import settings

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure upload folder
UPLOAD_FOLDER = Path(__file__).parent / 'data' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
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
                
                # Run the crew workflow
                result = run_crew_workflow(underperf_threshold, max_price_change)
                
                # Find latest output directory
                output_base = Path(settings.OUTPUT_DIR)
                output_dirs = sorted(output_base.glob('test_*'), key=os.path.getmtime, reverse=True)
                if output_dirs:
                    workflow_status['output_dir'] = str(output_dirs[0])
                
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
    """Preview CSV file content"""
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


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Starting Intelligent Management System Web Interface")
    print("=" * 80)
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Input folder: {settings.INPUT_DIR}")
    print(f"📁 Output folder: {settings.OUTPUT_DIR}")
    print("=" * 80)
    print("🌐 Open your browser and navigate to: http://localhost:5000")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
