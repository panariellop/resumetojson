# Use lightweight Python base image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies (if any) and python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the application port
EXPOSE 3333

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3333"]
