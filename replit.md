# Legal Document Analyzer

## Overview

This is a full-stack web application that simplifies legal documents by leveraging OCR (Optical Character Recognition) to extract text from uploaded images or PDFs, and then using Named Entity Recognition (NER) to identify key legal entities. The application provides users with a simplified summary of complex legal documents, making them more accessible and understandable.

The application accepts various file formats (PNG, JPG, JPEG, PDF, TIFF, BMP) and processes them through an OCR pipeline to extract text, followed by NLP processing to identify legal entities such as persons, organizations, dates, monetary amounts, and contract terms.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology Stack**: HTML5, CSS3, JavaScript (vanilla), Bootstrap 5.3.0
- **UI Framework**: Bootstrap for responsive design with custom CSS for styling
- **File Upload**: Drag-and-drop interface with traditional file picker fallback
- **User Experience**: Single-page application with progressive disclosure of results
- **Styling**: Custom CSS variables for consistent theming and modern gradient backgrounds

### Backend Architecture
- **Framework**: Flask (Python) with Werkzeug middleware for proxy handling
- **File Processing**: Secure file upload handling with size limits (16MB max) and extension validation
- **Modular Design**: Separate utility modules for OCR and NER processing
- **Error Handling**: Comprehensive logging and error response system
- **Session Management**: Flask sessions with configurable secret key

### Data Processing Pipeline
- **OCR Processing**: 
  - Tesseract OCR for text extraction from images
  - PyPDF2 for PDF text extraction
  - PIL (Pillow) for image preprocessing and format conversion
- **NER Processing**:
  - spaCy NLP library with English language model (en_core_web_sm)
  - Custom pattern matching for legal entity recognition
  - Entity categories: PERSON, ORG, DATE, MONEY, plus custom legal terms

### File Storage
- **Upload Directory**: Local file system storage in 'uploads' folder
- **File Security**: Secure filename handling with Werkzeug utilities
- **Temporary Processing**: Files processed and can be cleaned up after analysis

### API Structure
- **Main Routes**:
  - `GET /`: Serves the main application interface
  - `POST /upload`: Handles file upload and processing
- **Response Format**: JSON responses for AJAX interactions
- **Error Handling**: Structured error responses with appropriate HTTP status codes

## External Dependencies

### Core Python Libraries
- **Flask**: Web framework for backend API and routing
- **Werkzeug**: WSGI utilities for secure file handling and proxy support
- **pytesseract**: Python wrapper for Tesseract OCR engine
- **spaCy**: Advanced NLP library for named entity recognition
- **PIL (Pillow)**: Image processing and format conversion
- **PyPDF2**: PDF text extraction capabilities

### System Dependencies
- **Tesseract OCR**: External OCR engine (system-level installation required)
- **spaCy Language Model**: en_core_web_sm model for English text processing

### Frontend Dependencies
- **Bootstrap 5.3.0**: CSS framework delivered via CDN
- **Font Awesome 6.4.0**: Icon library delivered via CDN
- **Modern Browser APIs**: File API, Fetch API for file upload and processing

### Development Dependencies
- **Python Logging**: Built-in logging for debugging and monitoring
- **OS Environment Variables**: Configuration management for secrets and paths

### Third-party Services
- Currently designed for local/self-hosted deployment
- No external API dependencies for core functionality
- Extensible architecture allows for future AI service integration (placeholder exists for generative AI features)