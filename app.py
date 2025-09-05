import os
import logging
from flask import Flask, render_template, request, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import uuid
from utils.ocr_processor import OCRProcessor
from utils.ner_processor import NERProcessor
from utils.gemini_analyzer import GeminiAnalyzer
from utils.pdf_generator import ColorCodedPDFGenerator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff', 'bmp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize processors
ocr_processor = OCRProcessor()
ner_processor = NERProcessor()
gemini_analyzer = GeminiAnalyzer()
pdf_generator = ColorCodedPDFGenerator()

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page route."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No file was uploaded. Please select a file.'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'No file was selected. Please choose a file to upload.'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'File type not supported. Please upload: {", ".join(ALLOWED_EXTENSIONS).upper()}'
            }), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save the file
            file.save(filepath)
            
            try:
                # Extract text using OCR
                app.logger.info(f"Processing file: {unique_filename}")
                extracted_text = ocr_processor.extract_text(filepath)
                
                if not extracted_text.strip():
                    return jsonify({
                        'success': False,
                        'error': 'No text could be extracted from the document. Please ensure the image contains readable text.'
                    }), 400
                
                # Process entities using NER
                entities = ner_processor.extract_entities(extracted_text)
                
                # Analyze document with Gemini AI (with timeout protection)
                app.logger.info("Starting Gemini AI analysis...")
                try:
                    # Set a shorter timeout for Gemini analysis
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("Gemini analysis timed out")
                    
                    # Set 45 second timeout
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(45)
                    
                    try:
                        gemini_analysis = gemini_analyzer.analyze_document(extracted_text, entities)
                        summary = gemini_analysis.get('summary', 'Analysis not available')
                        clause_analysis = gemini_analysis.get('clauses', [])
                        risk_assessment = gemini_analysis.get('risk_assessment', {})
                        app.logger.info("Gemini analysis completed successfully")
                        
                        # Generate color-coded highlighted PDF (like original document with highlights)
                        try:
                            pdf_path = pdf_generator.generate_highlighted_document(
                                extracted_text, 
                                gemini_analysis, 
                                entities, 
                                filename
                            )
                            app.logger.info(f"Generated highlighted document: {pdf_path}")
                        except Exception as pdf_error:
                            app.logger.warning(f"Highlighted PDF generation failed: {pdf_error}")
                            pdf_path = None
                            
                    finally:
                        # Cancel the alarm
                        signal.alarm(0)
                        
                except (TimeoutError, Exception) as gemini_error:
                    app.logger.warning(f"Gemini analysis failed or timed out: {gemini_error}")
                    # Fallback to basic NER summary
                    summary = ner_processor.generate_basic_summary(extracted_text, entities)
                    clause_analysis = []
                    risk_assessment = {'level': 'unknown', 'description': 'AI analysis unavailable - using basic analysis'}
                    pdf_path = None
                
                # Clean up uploaded file
                try:
                    os.remove(filepath)
                except Exception as e:
                    app.logger.warning(f"Could not remove temporary file: {e}")
                
                return jsonify({
                    'success': True,
                    'data': {
                        'original_text': extracted_text,
                        'entities': entities,
                        'summary': summary,
                        'clause_analysis': clause_analysis,
                        'risk_assessment': risk_assessment,
                        'pdf_report': pdf_path,
                        'filename': filename
                    }
                })
                
            except Exception as processing_error:
                # Clean up file on processing error
                try:
                    os.remove(filepath)
                except:
                    pass
                
                app.logger.error(f"Processing error: {str(processing_error)}")
                return jsonify({
                    'success': False,
                    'error': f'Error processing document: {str(processing_error)}'
                }), 500
    
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

@app.route('/download-report/<path:filename>')
def download_report(filename):
    """Serve generated PDF reports."""
    try:
        from flask import send_file
        import os
        
        # Security: only allow files from reports directory
        safe_filename = secure_filename(filename)
        file_path = os.path.join('reports', safe_filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Report file not found.'
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"legal_analysis_{safe_filename}",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        app.logger.error(f"Report download error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Could not download report.'
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': 'File is too large. Maximum file size is 16MB.'
    }), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
