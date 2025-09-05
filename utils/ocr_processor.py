import pytesseract
from PIL import Image
import PyPDF2
import io
import logging
import os

class OCRProcessor:
    """Handles OCR text extraction from images and PDFs."""
    
    def __init__(self):
        """Initialize OCR processor."""
        self.logger = logging.getLogger(__name__)
        
        # Configure tesseract path if needed (for different environments)
        tesseract_cmd = os.environ.get('TESSERACT_CMD')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_text(self, file_path):
        """
        Extract text from image or PDF file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: Extracted text
        """
        try:
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return self._extract_from_pdf(file_path)
            else:
                return self._extract_from_image(file_path)
                
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {str(e)}")
            raise Exception(f"Could not extract text from document: {str(e)}")
    
    def _extract_from_image(self, file_path):
        """Extract text from image file using Tesseract OCR."""
        try:
            # Open and process image
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Configure OCR settings for better legal document recognition
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}"\'-$%&/@#'
            
            # Extract text
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Image OCR failed: {str(e)}")
            raise Exception(f"Could not process image: {str(e)}")
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF file."""
        try:
            text = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text + "\n"
            
            # If PDF text extraction yields little content, try OCR on PDF pages
            if len(text.strip()) < 50:
                self.logger.info("PDF text extraction yielded minimal content, attempting OCR")
                return self._ocr_pdf_pages(file_path)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"PDF processing failed: {str(e)}")
            raise Exception(f"Could not process PDF: {str(e)}")
    
    def _ocr_pdf_pages(self, file_path):
        """Apply OCR to PDF pages when text extraction fails."""
        try:
            import pdf2image
            
            # Convert PDF pages to images
            pages = pdf2image.convert_from_path(file_path)
            
            text = ""
            for page_num, page in enumerate(pages):
                # Apply OCR to each page
                page_text = pytesseract.image_to_string(page)
                text += f"Page {page_num + 1}:\n{page_text}\n\n"
            
            return text.strip()
            
        except ImportError:
            self.logger.warning("pdf2image not available, using basic PDF text extraction")
            return "PDF OCR requires pdf2image library. Please install it for better PDF processing."
        except Exception as e:
            self.logger.error(f"PDF OCR failed: {str(e)}")
            raise Exception(f"Could not perform OCR on PDF: {str(e)}")
