from flask import Flask, render_template, request, jsonify, session
from markupsafe import Markup
import pdfplumber
from google import generativeai as genai
import json
import difflib
import hashlib
import traceback
import os

GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/how_work')
def howitwork():
    return render_template('how_it_work.html')

@app.route('/summary_analysis')
def summary_analysis():
    return render_template('summary_.html')

def extract_json_from_response(response_text):
    """Extract JSON array from Gemini response text - SIMPLIFIED VERSION"""
    # STEP 1: Clean up markdown
    if '```':
        start_pos = response_text.find('```json') + 7
        end_pos = response_text.rfind('```')
        if end_pos > start_pos:
            response_text = response_text[start_pos:end_pos]
            
    # STEP 2: Simple cleanup
    response_text = response_text.strip()
    if response_text.lower().startswith('json'):
        response_text = response_text[4:].strip()
    # Remove any backticks
    response_text = response_text.strip('`\n\r\t ')
    
    # STEP 3: Find the first [ and last ]
    start_bracket = response_text.find('[')
    end_bracket = response_text.rfind(']')
    
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        json_content = response_text[start_bracket:end_bracket + 1]
    else:
        json_content = response_text
   
    # STEP 4: Parse and return
    try:
        parsed_data = json.loads(json_content)
        
        # SIMPLE VALIDATION - NO COMPLEX FLATTENING
        if isinstance(parsed_data, list):
            # Just check if we have items and they're dicts
            if parsed_data:
                for i, item in enumerate(parsed_data):
                    if not isinstance(item, dict):
                        # If it's a list, something is wrong with our parsing
                        if isinstance(item, list):
                            # Just return the first valid list of dicts we find
                            for nested_item in parsed_data:
                                if isinstance(nested_item, list) and nested_item and isinstance(nested_item, dict):
                                     return nested_item
                            raise ValueError("Cannot find valid dict structure")
                        else:
                            raise ValueError(f"Expected dict, got {type(item)}")
             
                return parsed_data
            else:
                return []
        
        elif isinstance(parsed_data, dict):
            return [parsed_data]
        else:
            raise ValueError(f"Expected list or dict, got {type(parsed_data)}")
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

def find_best_match(original_text, clause_text):
    seq = difflib.SequenceMatcher(None, original_text, clause_text)
    match = seq.find_longest_match(0, len(original_text), 0, len(clause_text))
    if match.size == 0:
        return None
    return original_text[match.a: match.a + match.size]

def generate_highlighted_html(original_text, clauses_data):
    highlighted_text = original_text
    risk_class_map = {
        'green': 'highlight-green',
        'yellow': 'highlight-yellow',
        'red': 'highlight-red'
    }
    for index, clause in enumerate(clauses_data):
        clause_text = clause.get('text', '')
        risk_level = clause.get('riskLevel', 'medium').strip().lower()
        highlight_class = risk_class_map.get(risk_level, 'highlight-yellow')
        highlighted_span = f'<span class="{highlight_class}" data-clause-id="{index}" onclick="showClausePopup({index})" title="Click for details">{clause_text}</span>'
        
        match_text = find_best_match(highlighted_text, clause_text)
        if match_text:
            # Replace only first approx match
            highlighted_text = highlighted_text.replace(match_text, highlighted_span, 1)
        else:
            print(f"Warning: No approximate match found for clause starting '{clause_text[:30]}'")
            
    return highlighted_text

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # File processing (your existing code)
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        filename = file.filename 
        # Extract text from PDF
        text = ""
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as pdf_error:
            return jsonify({'success': False, 'error': f'Error reading PDF: {str(pdf_error)}'}), 400
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'No text found in PDF'}), 400
        
        # Add debug print to see what we're working with
        # AI prompt
        prompt = f"""
            You are an expert legal assistant. Analyze the legal document and return a valid JSON array.
            Each element should be a JSON object with these exact keys:
            - "documentType": string (e.g., "Rental Agreement")
            - "lawyerSpecialty": string (e.g., "Real Estate Lawyer")  
            - "text": string (exact clause text from document)
            - "riskLevel": string (use Green: Standard and fair clauses.

            Yellow: Clauses that are negotiable or require clarification. A pop-up would suggest questions to ask, like, "Could you clarify the terms for early termination?"

            Red: High-risk or unusual clauses that could pose significant financial or legal risks.)
            - "explanation": string (brief explanation)
            - "suggestions": array of strings (practical questions/advice)

            Return ONLY valid JSON array, no other text.

            Document: {text[:1000000]}
            """

        # Bulletproof AI call with fallback
        try:
            response = model.generate_content(prompt)
            api_response_text = response.text.strip()
           
            # Check if it's an error response
            if not api_response_text or api_response_text.startswith('<') or 'quota' in api_response_text.lower():
                raise Exception(f"API returned error: {api_response_text[:200]}")
                
        except Exception as api_error:
            pass
            
        #  Safe JSON parsing with detailed error handling
        try:
            clauses_data = extract_json_from_response(api_response_text)
            # Ensure it's a list of dictionaries
            if not isinstance(clauses_data, list):
                raise ValueError(f"Expected list, got {type(clauses_data)}")
            
            if not clauses_data: 
                raise ValueError("Got empty list from JSON parsing")
                
            # Validate first element is a dictionary
            if clauses_data and not isinstance(clauses_data[0], dict):
                raise ValueError(f"First element is {type(clauses_data[0])}, expected dict")
                
        except Exception as parse_error:
            # Return the error with raw response for debugging
            return jsonify({
                'success': False,
                'error': f'Failed to parse AI response. Error: {str(parse_error)}. Raw response: {api_response_text[:200]}...'
            }), 500

        # Safe HTML generation
        try:
            highlighted_html = generate_highlighted_html(text, clauses_data)
        except Exception as highlight_error:
            highlighted_html = text 

        # Safe metadata extraction (THIS WAS THE FAILING LINE)
        document_type = "Legal Document"
        lawyer_specialty = "Legal Professional"
        
        if clauses_data and len(clauses_data) > 0:
            first_clause = clauses_data[0]
           
            # Check if it's actually a dictionary
            if isinstance(first_clause, dict):
                document_type = first_clause.get('documentType', document_type)
                lawyer_specialty = first_clause.get('lawyerSpecialty', lawyer_specialty)
            else:
                pass
               
        return jsonify({
            'success': True,
            'data': {
                'filename': filename,
                'documentType': document_type,
                'lawyerSpecialty': lawyer_specialty,
                'originalText': text,
                'highlightedHtml': highlighted_html,
                'clauses': clauses_data,
                'summary': f"Document analyzed successfully. Found {len(clauses_data)} clauses for review.",
                'totalClauses': len(clauses_data)
            }
        })

    except Exception as e:
       
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

USERS = {
    "kirti@example.com": {
        "password": hashlib.sha256("kirti123".encode()).hexdigest(),
        "premium": True
    }
}
 
@app.route('/summariser', methods=['POST'])
def summarize_file():
    try:
        # Check if file part exists
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.lower().endswith(".pdf"):
            return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

        text = ""
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as pdf_error:
            return jsonify({'success': False, 'error': f'Error reading PDF: {str(pdf_error)}'}), 400

        if not text.strip():
            return jsonify({'success': False, 'error': 'No text found in PDF'}), 400

        # Build prompt
        prompt = f"""
        You are a highly skilled legal assistant.
        Your task is to carefully analyze the following document and produce a structured legal summary.

        Instructions:

        Begin the summary directly with the title or structured content (e.g., “Legal Services Agreement Summary”), without prefatory phrases such as “Here is the summary” or “The following is…”.

        Extract only legally relevant information (facts, issues, arguments, clauses, statutes, decisions).

        Use formal and legally appropriate terminology.

        Present the summary in a structured format, such as:

        Title of Document / Agreement Summary

        Effective Date & Parties

        Key Terms / Facts

        Obligations & Rights

        Legal Issues / Clauses of Note

        Conclusions / Decisions

        Write in neutral, objective, and concise language.

        Text to Summarize:
        {text[:1000000]}
        """

        # Generate summary
        response = model.generate_content(prompt)
        summary_response = response.text.strip()

        return jsonify({
            'success': True,
            'data': {
                'filename': file.filename,
                'summary': summary_response
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/login', methods=['GET','POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        # Hash the provided password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials
        user = USERS.get(email)
        if user and user['password'] == password_hash:
            # Store in session
            session['user_email'] = email
            session['authenticated'] = True
            session['premium'] = user.get('premium', False)
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'premium': user.get('premium', False)
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    referrer_url = request.referrer  
    if request.method == 'GET':
        return render_template('signup.html', referrer=referrer_url)
   
    try:
        data = request.get_json()
        fullname = data.get('fullname', '')
        phone = data.get('phone', '')
        email = data.get('email', '')
        password = data.get('password')
        if not fullname or not phone or not email or not password:
            return jsonify({'success': False, 'error': 'All fields except newsletter are required.'}), 400
        if email in USERS:
            pass
            return jsonify({'success': False, 'error': 'Email already exists.'}), 400
        USERS[email] = {
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "fullname": fullname,
            "phone": phone,
            "premium": False
        }

        return jsonify({'success': True, 'message': 'User registered successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

app.secret_key = 'your-secret-key-here'

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)



