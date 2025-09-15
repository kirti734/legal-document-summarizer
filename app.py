from flask import Flask, render_template, request, jsonify, session
from markupsafe import Markup
import pdfplumber
from google import generativeai as genai
import json
import re
import hashlib

GOOGLE_API_KEY = "AIzaSyCmRa47fFyxZ8ajizSJIJRprlqhuT7KemA"  # Replace with your actual key

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result')
def result():
    return render_template('result.html')

def extract_json_from_response(response_text):
    """Extract JSON array from Gemini response text - SIMPLIFIED VERSION"""
    
    # print(f"Raw response (first 200 chars): {response_text[:200]}...")
    
    # STEP 1: Clean up markdown
    if '```':
        start_pos = response_text.find('```json') + 7
        end_pos = response_text.rfind('```')
        if end_pos > start_pos:
            response_text = response_text[start_pos:end_pos]
            # print("✅ Removed markdown wrapper")
    
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
        # print(f"✅ Extracted JSON array: {json_content[:100]}...")
    else:
        json_content = response_text
    
    # print(f"Final JSON to parse: {json_content}")
    
    # STEP 4: Parse and return
    try:
        parsed_data = json.loads(json_content)
        # print(f"✅ Parsed successfully. Type: {type(parsed_data)}")
        
        # 🔥 SIMPLE VALIDATION - NO COMPLEX FLATTENING
        if isinstance(parsed_data, list):
            # print(f"📋 Got list with {len(parsed_data)} items")
            
            # Just check if we have items and they're dicts
            if parsed_data:
                for i, item in enumerate(parsed_data):
                    # print(f"Item {i} type: {type(item)}")
                    if not isinstance(item, dict):
                        # print(f"❌ Item {i} is {type(item)}, not dict: {item}")
                        # If it's a list, something is wrong with our parsing
                        if isinstance(item, list):
                            # print("🔄 Detected nested structure, trying to fix...")
                            # Just return the first valid list of dicts we find
                            for nested_item in parsed_data:
                                if isinstance(nested_item, list) and nested_item and isinstance(nested_item, dict):
                                    # print("✅ Found valid nested array")
                                    return nested_item
                            raise ValueError("Cannot find valid dict structure")
                        else:
                            raise ValueError(f"Expected dict, got {type(item)}")
                
                # print("✅ All items are dictionaries")
                return parsed_data
            
            else:
                # print("📋 Empty list")
                return []
        
        elif isinstance(parsed_data, dict):
            # print("📝 Single dict, wrapping in list")
            return [parsed_data]
        
        else:
            raise ValueError(f"Expected list or dict, got {type(parsed_data)}")
            
    except json.JSONDecodeError as e:
        # print(f"❌ JSON parsing failed: {e}")
        # print(f"Attempted to parse: {json_content}")
        raise ValueError(f"Invalid JSON: {e}")


def generate_highlighted_html(original_text, clauses_data):
    """Generate HTML with highlighted clauses"""
    if not clauses_data or not isinstance(clauses_data, list):
        # print(f"Warning: clauses_data is not a list: {type(clauses_data)}")
        return original_text
    
    highlighted_text = original_text
    
    # Add type checking for each clause
    valid_clauses = []
    for clause in clauses_data:
        if isinstance(clause, dict):
            valid_clauses.append(clause)
        else:
            print(f"Warning: Clause is not a dict: {type(clause)} - {clause}")
    
    if not valid_clauses:
        return original_text
    
    # Sort clauses by text length (longest first)
    sorted_clauses = sorted(valid_clauses, key=lambda x: len(x.get('text', '')), reverse=True)
    
    for index, clause in enumerate(sorted_clauses):
        clause_text = clause.get('text', '') if isinstance(clause, dict) else ''
        if not clause_text:
            continue
            
        risk_level = clause.get('riskLevel', 'medium').lower()
        
        # Risk level to CSS class mapping
        risk_class_map = {
            'green': 'highlight-green',
            'yellow': 'highlight-yellow', 
            'red': 'highlight-red'
        }
        
        highlight_class = risk_class_map.get(risk_level, 'highlight-yellow')
        highlighted_span = f'<span class="{highlight_class}" data-clause-id="{index}" onclick="showClausePopup({index})" title="Click for details">{clause_text}</span>'
        
        if clause_text in highlighted_text:
            highlighted_text = highlighted_text.replace(clause_text, highlighted_span, 1)
    
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
        
        # 🔥 FIX 1: Add debug print to see what we're working with
        # print(f"Extracted text length: {len(text)}")
        
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

Document: {text[:2000]}
"""

        # 🔥 FIX 2: Bulletproof AI call with fallback
        try:
            # print("=== CALLING GEMINI API ===")
            response = model.generate_content(prompt)
            api_response_text = response.text.strip()
            # print(f"API Response type: {type(api_response_text)}")
            # print(f"API Response (first 100 chars): {api_response_text[:100]}")
            
            # Check if it's an error response
            if not api_response_text or api_response_text.startswith('<') or 'quota' in api_response_text.lower():
                raise Exception(f"API returned error: {api_response_text[:200]}")
                
        except Exception as api_error:
            # print(f"=== API ERROR: {str(api_error)} ===")
            
            # Use mock data when API fails
            clauses_data = [
                {
                    "documentType": "Legal Document (API Unavailable)",
                    "lawyerSpecialty": "General Lawyer",
                    "text": "standard legal clause",
                    "riskLevel": "yellow",
                    "explanation": "API quota exceeded - showing sample analysis",
                    "suggestions": ["Wait for API quota reset", "Try again in a few minutes"]
                }
            ]
            
            # print(f"Using mock data: {len(clauses_data)} clauses")
            
            # Simple highlighting for mock data
            highlighted_html = text.replace("clause", '<span class="highlight-yellow" data-clause-id="0" onclick="showClausePopup(0)">clause</span>')
            
            return jsonify({
                'success': True,
                'data': {
                    'filename': filename,
                    'documentType': clauses_data[0]['documentType'],
                    'lawyerSpecialty': clauses_data[0]['lawyerSpecialty'],
                    'originalText': text,
                    'highlightedHtml': highlighted_html,
                    'clauses': clauses_data,
                    'summary': f"Document processed with fallback analysis (API unavailable).",
                    'totalClauses': len(clauses_data)
                }
            })

        # 🔥 FIX 3: Safe JSON parsing with detailed error handling
        try:
            clauses_data = extract_json_from_response(api_response_text)
            # print(f"Parsed clauses_data type: {type(clauses_data)}")
            # print(f"Parsed clauses_data length: {len(clauses_data) if isinstance(clauses_data, list) else 'Not a list'}")
            
            # 🔥 CRITICAL: Ensure it's a list of dictionaries
            if not isinstance(clauses_data, list):
                # print(f"ERROR: clauses_data is {type(clauses_data)}, not list")
                # print(f"Content: {str(clauses_data)[:200]}")
                raise ValueError(f"Expected list, got {type(clauses_data)}")
            
            if not clauses_data:  # Empty list
                raise ValueError("Got empty list from JSON parsing")
                
            # Validate first element is a dictionary
            if clauses_data and not isinstance(clauses_data[0], dict):
                # print(f"ERROR: First element is {type(clauses_data[0])}, not dict")
                # print(f"First element content: {clauses_data[0]}")
                raise ValueError(f"First element is {type(clauses_data[0])}, expected dict")
                
        except Exception as parse_error:
            # print(f"=== JSON PARSING ERROR: {str(parse_error)} ===")
            # print(f"Raw API response: {api_response_text[:500]}")
            
            # Return the error with raw response for debugging
            return jsonify({
                'success': False,
                'error': f'Failed to parse AI response. Error: {str(parse_error)}. Raw response: {api_response_text[:200]}...'
            }), 500

        # 🔥 FIX 4: Safe HTML generation
        try:
            highlighted_html = generate_highlighted_html(text, clauses_data)
        except Exception as highlight_error:
            # print(f"=== HIGHLIGHTING ERROR: {str(highlight_error)} ===")
            highlighted_html = text  # Fallback to plain text

        # 🔥 FIX 5: Safe metadata extraction (THIS WAS THE FAILING LINE)
        document_type = "Legal Document"
        lawyer_specialty = "Legal Professional"
        
        if clauses_data and len(clauses_data) > 0:
            first_clause = clauses_data[0]
            # print(f"First clause type: {type(first_clause)}")
            # print(f"First clause content: {first_clause}")
            
            # 🔥 SAFE ACCESS: Check if it's actually a dictionary
            if isinstance(first_clause, dict):
                document_type = first_clause.get('documentType', document_type)
                lawyer_specialty = first_clause.get('lawyerSpecialty', lawyer_specialty)
            else:
                print(f"WARNING: First clause is not a dict, it's {type(first_clause)}")
        
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
        # print(f"=== GENERAL UPLOAD ERROR: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

USERS = {
    "demo@example.com": {
        "password": hashlib.sha256("demo123".encode()).hexdigest(),
        "premium": False
    },
    "kirti@example.com": {
        "password": hashlib.sha256("kirti123".encode()).hexdigest(),
        "premium": True
    }
}

@app.route('/login', methods=['POST'])
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
    if request.method == 'GET':
        return render_template('signup.html')
    
    try:
        data = request.get_json()
        fullname = data.get('fullname', '')
        phone = data.get('phone', '')
        email = data.get('email', '')
        password = data.get('password')
        subscribe = data.get('subscribeNewsletter', False)
        if not fullname or not phone or not email or not password:
            return jsonify({'success': False, 'error': 'All fields except newsletter are required.'}), 400
        if email in USERS:
            return jsonify({'success': False, 'error': 'Email already exists.'}), 400
        USERS[email] = {
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "fullname": fullname,
            "phone": phone,
            "newsletter": subscribe,
            "premium": False
        }
        return jsonify({'success': True, 'message': 'User registered successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# Your existing routes...
app.secret_key = 'your-secret-key-here'

if __name__ == '__main__':
    app.run(debug=True)
