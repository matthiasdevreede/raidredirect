FROM python:3.10

WORKDIR /app

# Install dependencies first (cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of project
COPY . .

CMD ["python", "src/main.py"]
