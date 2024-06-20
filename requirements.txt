# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages
RUN pip install -r requirements.txt

# Expose the ports for Streamlit and FastAPI
EXPOSE 8501
EXPOSE 8000

# Run the streamlit app and FastAPI backend
CMD ["sh", "-c", "uvicorn backend:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
