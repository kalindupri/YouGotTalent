FROM python:3.12-slim

WORKDIR /app

# ffmpeg compresses uploaded video/audio auditions before they're stored (see
# app/core/media_processing.py) to keep Azure Blob storage/egress costs down.
# fonts-dejavu-core provides the bold sans-serif font used to render marketing post images
# (see app/core/marketing_image.py) — Pillow has no built-in scalable font of its own.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fix CRLF line endings that Windows editors may introduce
RUN sed -i 's/\r//' entrypoint.sh && chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
