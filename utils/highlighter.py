import fitz  # PyMuPDF
from your_gemini_module import GeminiAnalyzer  # Replace with actual import
import logging

# Initialize Gemini analyzer
analyzer = GeminiAnalyzer()

# Load your document text and entities (extract entities with your NLP pipeline)
document_text = """Your full document text here..."""
entities = {}  # Your extracted entities dictionary

# Get analysis result from Gemini
analysis_result = analyzer.analyze_document(document_text, entities)

# Extract clauses from result
clauses = analysis_result.get('clauses', [])

highlight_colors = {
    "harmful": (1, 0, 0),       # Red
    "warning": (1, 1, 0),       # Yellow
    "good": (0, 1, 0),          # Green
    "neutral": (0.9, 0.9, 0.9)  # Light gray
}

input_pdf_path = "input.pdf"
output_pdf_path = "output_highlighted.pdf"

doc = fitz.open(input_pdf_path)

for page in doc:
    for clause in clauses:
        clause_text = clause["text"]
        classification = clause.get("classification", "neutral")
        color = highlight_colors.get(classification, (1, 1, 1))
        rects = page.search_for(clause_text)
        for rect in rects:
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(stroke=color)
            highlight.update()

doc.save(output_pdf_path)
print(f"Saved highlighted PDF as {output_pdf_path}")
