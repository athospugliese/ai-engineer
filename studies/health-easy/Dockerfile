FROM python:3.9

WORKDIR /app

# Create vectorstore directory
RUN mkdir -p vectorstore/masp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 

CMD ["uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]