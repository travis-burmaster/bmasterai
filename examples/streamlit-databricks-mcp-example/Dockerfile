FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 nonroot && chown -R nonroot:nonroot /app
USER nonroot

EXPOSE 8501
CMD ["streamlit", "run", "enhanced_app.py", "--server.address", "0.0.0.0"]
