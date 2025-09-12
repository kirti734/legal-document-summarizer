import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import uuid
from utils.ocr_processor import OCRProcessor
from utils.ner_processor import NERProcessor
from utils.gemini_analyzer import GeminiAnalyzer
from utils.pdf_generator import ColorCodedPDFGenerator

# Logging setup
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Config
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'    # <-- New directory to save generated PDFs
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff', 'bmp'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)  # Make reports folder as well

# Initialize processors
ocr_processor = OCRProcessor()
ner_processor = NERProcessor()
gemini_analyzer = GeminiAnalyzer()
pdf_generator = ColorCodedPDFGenerator()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded.'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400
        if not allowed_file(file.filename):
            return jsonify({'success': False,
                            'error': f'File type not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS).upper()}'}), 400
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Extract text using OCR
        extracted_text = ocr_processor.extract_text(filepath)
        if not extracted_text.strip():
            return jsonify({'success': False,
                            'error': 'No readable text extracted from document.'}), 400
        
        entities = ner_processor.extract_entities(extracted_text)

        # Gemini AI analysis with timeout
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("Gemini analysis timed out")
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(45)  # 45 second timeout

        try:
            gemini_analysis = gemini_analyzer.analyze_document(extracted_text, entities)
            summary = gemini_analysis.get('summary', 'Analysis not available')
            clause_analysis = gemini_analysis.get('clauses', [])
            risk_assessment = gemini_analysis.get('risk_assessment', {})
            # Generate and save report PDF inside reports folder
            pdf_report_name = f"{uuid.uuid4().hex}_highlighted.pdf"
            pdf_report_path = os.path.join(REPORTS_FOLDER, pdf_report_name)
            pdf_generator.generate_highlighted_document(
                extracted_text, gemini_analysis, entities, pdf_report_path
            )
            signal.alarm(0)  # Cancel alarm
        except Exception as e:
            signal.alarm(0)
            # On error or timeout fallback
            summary = ner_processor.generate_basic_summary(extracted_text, entities)
            clause_analysis = []
            risk_assessment = {'level': 'unknown', 'description': 'AI analysis unavailable - basic analysis'}
            pdf_report_path = None

        # Remove uploaded file
        try:
            os.remove(filepath)
        except Exception as e:
            app.logger.warning(f"Could not remove temp file: {e}")

        # URL to serve generated PDF report (relative to app root)
        pdf_report_url = f"/download-report/{pdf_report_name}" if pdf_report_path else None

        return jsonify({
            'success': True,
            'data': {
                'original_text': extracted_text,
                'entities': entities,
                'summary': summary,
                'clause_analysis': clause_analysis,
                'risk_assessment': risk_assessment,
                'pdf_report_url': pdf_report_url
            }
        })

    except Exception as e:
        app.logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred.'}), 500

@app.route('/download-report/<filename>')
def download_report(filename):
    safe_filename = secure_filename(filename)
    file_path = os.path.join(REPORTS_FOLDER, safe_filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'Report file not found.'}), 404
    return send_file(file_path, mimetype='application/pdf')

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'File too large. Max 16MB.'}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
