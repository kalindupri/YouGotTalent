FROM python:3.12-slim

WORKDIR /app

# ffmpeg compresses uploaded video/audio auditions before they're stored (see
# app/core/media_processing.py) to keep Azure Blob storage/egress costs down.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fix CRLF line endings that Windows editors may introduce
RUN sed -i 's/\r//' entrypoint.sh && chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
