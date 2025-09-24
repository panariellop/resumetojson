from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import anthropic
import os
import base64
import logging
import re
import json
import io
from json_repair import repair_json
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, Dict, Any, Union
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PDF resume to JSON", description="Upload PDF and get it back as json")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def json_block_to_dict(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely extract and parse JSON with comprehensive error handling
    """
    if not text:
        return None
    
    try:
        # Try to find JSON block
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if not match:
            # Fallback: try to find raw JSON object
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if not match:
                return None
        
        json_string = match.group(1).strip()
        
        # Parse to dict
        return json.loads(json_string)
        
    except (AttributeError, json.JSONDecodeError, TypeError) as e:
        print(f"Failed to extract/parse JSON: {e}")
        return None

def extract_json_markdown_block(text):
    """
    Extract the \`\`\`json<stuff>\`\`\` portion of the response
    """
    patterns = [
        r'```json\s*(.*?)\s*```',  # ```json ... ```
        r'```JSON\s*(.*?)\s*```',  # ```JSON ... ```
        r'```\s*(.*?)\s*```',       # ``` ... ``` (any code block)
        r'\{.*\}',                  # Raw JSON object (greedy, single line)
    ]
    
    for pattern in patterns:
        if pattern == r'\{.*\}':
            # For raw JSON, use different flags
            match = re.search(pattern, text, re.DOTALL)
        else:
            match = re.search(pattern, text, re.DOTALL)
        
        if match:
            try:
                json_str = match.group(1) if '```' in pattern else match.group(0)
                # Validate it's actual JSON
                json.loads(json_str.strip())
                return json_str.strip()
            except (json.JSONDecodeError, IndexError):
                continue
    
    return None

def compress_pdf(pdf_bytes: bytes, target_size_kb: int = 100) -> bytes:
    """
    Compress PDF by extracting text and creating a new minimal PDF
    """
    try:
        logger.info(f"Original PDF size: {len(pdf_bytes)} bytes")
        
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text_content = ""
        
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        logger.info(f"Extracted text length: {len(text_content)} characters")
        
        # Create a new compressed PDF with just the text
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Split text into lines and pages
        lines = text_content.split('\n')
        y_position = height - 40
        line_height = 12
        margin = 40
        
        for line in lines:
            # Handle long lines by wrapping
            if len(line) > 80:
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) < 80:
                        current_line += word + " "
                    else:
                        if current_line:
                            c.drawString(margin, y_position, current_line.strip())
                            y_position -= line_height
                            if y_position < margin:
                                c.showPage()
                                y_position = height - 40
                        current_line = word + " "
                
                if current_line:
                    c.drawString(margin, y_position, current_line.strip())
                    y_position -= line_height
            else:
                c.drawString(margin, y_position, line)
                y_position -= line_height
            
            # Start new page if needed
            if y_position < margin:
                c.showPage()
                y_position = height - 40
        
        c.save()
        compressed_pdf = buffer.getvalue()
        
        logger.info(f"Compressed PDF size: {len(compressed_pdf)} bytes")
        
        # If still too large, truncate text and try again
        if len(compressed_pdf) > target_size_kb * 1024:
            logger.info("PDF still too large, truncating text content")
            max_chars = int(len(text_content) * (target_size_kb * 1024) / len(compressed_pdf) * 0.8)
            truncated_text = text_content[:max_chars] + "\n... [content truncated]"
            
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            
            lines = truncated_text.split('\n')
            y_position = height - 40
            
            for line in lines:
                if len(line) > 80:
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            if current_line:
                                c.drawString(margin, y_position, current_line.strip())
                                y_position -= line_height
                                if y_position < margin:
                                    c.showPage()
                                    y_position = height - 40
                            current_line = word + " "
                    
                    if current_line:
                        c.drawString(margin, y_position, current_line.strip())
                        y_position -= line_height
                else:
                    c.drawString(margin, y_position, line)
                    y_position -= line_height
                
                if y_position < margin:
                    c.showPage()
                    y_position = height - 40
            
            c.save()
            compressed_pdf = buffer.getvalue()
            logger.info(f"Final compressed PDF size: {len(compressed_pdf)} bytes")
        
        return compressed_pdf
        
    except Exception as e:
        logger.error(f"Error compressing PDF: {str(e)}")
        # Return original if compression fails
        return pdf_bytes

def resume_to_json(pdf_bytes: bytes, prompt: str, attempt: int = 0, max_attempts: int = 5):
    """Send PDF directly to LLM for processing"""
    try:
        
        # Initialize Anthropic client with API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            raise HTTPException(status_code=500, detail="API key not configured")
            
        client = anthropic.Anthropic(api_key=api_key)
        
        # Compress PDF before sending to LLM
        logger.info("Compressing PDF before sending to LLM...")
        compressed_pdf_bytes = compress_pdf(pdf_bytes, target_size_kb=10)
        
        # Extract and log the compressed text content for debugging
        try:
            compressed_pdf_reader = PyPDF2.PdfReader(io.BytesIO(compressed_pdf_bytes))
            compressed_text = ""
            for page in compressed_pdf_reader.pages:
                compressed_text += page.extract_text() + "\n"
            
            logger.info(f"Compressed PDF text content (first 500 chars): {compressed_text[:500]}...")
            logger.info(f"Total compressed text length: {len(compressed_text)} characters")
        except Exception as e:
            logger.warning(f"Could not extract text from compressed PDF for logging: {str(e)}")
        
        # Encode compressed PDF to base64 for LLM API
        pdf_base64 = base64.b64encode(compressed_pdf_bytes).decode('utf-8')
        
        # Send request to LLM API
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64
                            }
                        }
                    ]
                }
            ]
        )
        
        response_text = message.content[0].text

        match = json_block_to_dict(extract_json_markdown_block(response_text))
        if not match and attempt < max_attempts:
            return resume_to_json(pdf_bytes, prompt, attempt + 1, max_attempts)
        return match 
        
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in LLM processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing with LLM: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve a simple landing page explaining the service."""
    html_content = open("./public/index.html").read()
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"message": "PDF to LLM API is running", "status": "healthy"}

@app.post("/resume-to-json/")
async def process_pdf(
    file: UploadFile = File(...),
):
    """Upload PDF and process with LLM"""
    prompt = open("./prompt.md").read()
    
    # Validate file extension
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Check if API key is configured
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY environment variable not set")
    
    try:
        # Read the uploaded file
        pdf_bytes = await file.read()
        
        # Validate file is not empty
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty PDF file")
        
        # Process with LLM
        llm_response = resume_to_json(pdf_bytes, prompt, attempt=0, max_attempts=5)
        
        # Prepare response
        response_data = {
            "filename": file.filename,
            "file_size_bytes": len(pdf_bytes),
            "resume": llm_response
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    # Start the FastAPI server when running directly
    import uvicorn
    logger.info("Starting FastAPI server with hot reload...")
    logger.info("Server will be available at: http://127.0.0.1:8000")
    logger.info("API documentation available at: http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
