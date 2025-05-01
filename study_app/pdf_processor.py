import PyPDF2
import os
import re
from flask import current_app

def process_pdf_file(file_path):
    """
    Extract text from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content from the PDF
    """
    try:
        extracted_text = extract_text_from_pdf(file_path)
        processed_text = clean_and_chunk_text(extracted_text)
        return processed_text
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return "Error extracting text from PDF. Please ensure the file is not corrupted or password protected."

def extract_text_from_pdf(file_path):
    """
    Extract text content from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Raw extracted text
    """
    text = ""
    
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise

def clean_and_chunk_text(text, max_chunk_size=8000):
    """
    Clean and chunk text to prepare for AI processing.
    
    Args:
        text (str): Raw extracted text from PDF
        max_chunk_size (int): Maximum size for each text chunk
        
    Returns:
        str: Cleaned and processed text
    """
    # Basic cleaning
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Fix common OCR issues
    text = text.replace('|', 'I').replace('1', 'l')
    
    # If text is too long, chunk it (for large documents)
    if len(text) > max_chunk_size:
        # This is a simple chunking method - more sophisticated methods could be used
        chunks = []
        start = 0
        
        while start < len(text):
            # Find a good break point (end of sentence)
            end = min(start + max_chunk_size, len(text))
            if end < len(text):
                # Try to find a sentence break
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + max_chunk_size // 2:  # Only use if we found a reasonable break
                    end = sentence_end + 1
            
            chunks.append(text[start:end])
            start = end
        
        # For simplicity in this example, we're just taking the first chunk
        # In a real application, you might want to process all chunks or find a better way to summarize
        return chunks[0]
    
    return text