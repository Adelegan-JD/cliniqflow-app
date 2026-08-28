# # FROM python:3.11-slim
# # Change from python:3.11-slim to an explicit stable build
# FROM python:3.11-slim-bookworm


# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1

# WORKDIR /app

# # RUN sed -i 's|http://deb.debian.org|https://debian.org|g' /etc/apt/sources.list.d/debian.sources

# # RUN apt-get update \
# #     && apt-get install -y --no-install-recommends \
# #         build-essential \
# #         ffmpeg \
# #         libsndfile1 \
# #         git \
# #     && rm -rf /var/lib/apt/lists/*

# # RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources

# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         build-essential \
#         ffmpeg \
#         libsndfile1 \
#         git \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8001

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]



# FROM python:3.11-slim-bookworm

# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1

# WORKDIR /app

# # Overwrite default mirrors with Cloudflare's secure HTTPS endpoints
# # RUN echo -e "Types: deb\nURIs: https://cloudflaremirrors.com\nSuites: bookworm bookworm-updates\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\nTypes: deb\nURIs: https://cloudflaremirrors.com-security\nSuites: bookworm-security\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg" > /etc/apt/sources.list.d/debian.sources

# RUN printf '%s\n' \
#   'Types: deb' \
#   'URIs: http://mirrors.edge.kernel.org/debian' \
#   'Suites: bookworm bookworm-updates' \
#   'Components: main' \
#   'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
#   '' \
#   'Types: deb' \
#   'URIs: http://mirrors.edge.kernel.org/debian-security' \
#   'Suites: bookworm-security' \
#   'Components: main' \
#   'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
#   > /etc/apt/sources.list.d/debian.sources


# # Run update and install system packages
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         build-essential \
#         ffmpeg \
#         libsndfile1 \
#         git \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8001

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

# Convert the approved Hugging Face checkpoint during image build.  The final
# runtime image does not contain PyTorch, Transformers, or Hugging Face tools.
FROM python:3.11-slim-bookworm AS model-converter
RUN pip install --no-cache-dir ctranslate2==4.6.2 transformers==4.49.0 torch==2.6.0
RUN ct2-transformers-converter \
    --model LyngualLabs/whisper-small-yoruba \
    --output_dir /opt/models/yoruba-whisper-small-ct2 \
    --quantization int8

# Use an official lightweight Python image
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/cliniq

# Set the working directory inside the container
WORKDIR /app

RUN addgroup --system cliniq && adduser --system --ingroup cliniq --home /home/cliniq cliniq

# librosa needs these to reliably decode browser-generated webm recordings.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first (for faster rebuilds)
COPY requirements.txt .

# Install all Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=model-converter /opt/models/yoruba-whisper-small-ct2 /opt/models/yoruba-whisper-small-ct2

# Copy the rest of the application code
COPY . .

RUN chown -R cliniq:cliniq /app /home/cliniq
USER cliniq

# Tell Docker which port this service listens on
EXPOSE 8001

# The command to start the AI engine
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
