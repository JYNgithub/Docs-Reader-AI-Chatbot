# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and clean up in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install in one step
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Preload Chroma ONNX model via a fake call
RUN python -c "\
import chromadb; \
client = chromadb.PersistentClient(path='/root/.cache/chroma'); \
collection = client.create_collection('dummy-collection'); \
collection.add(documents=['This is a dummy document'], ids=['doc1']); \
collection.query(query_texts=['This is a query document'], n_results=1) \
"

# Copy app and vectors
COPY . .
COPY vectors /app/vectors

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
