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



FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Overwrite default mirrors with Cloudflare's secure HTTPS endpoints
# RUN echo -e "Types: deb\nURIs: https://cloudflaremirrors.com\nSuites: bookworm bookworm-updates\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\nTypes: deb\nURIs: https://cloudflaremirrors.com-security\nSuites: bookworm-security\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg" > /etc/apt/sources.list.d/debian.sources

RUN printf '%s\n' \
  'Types: deb' \
  'URIs: http://mirrors.edge.kernel.org/debian' \
  'Suites: bookworm bookworm-updates' \
  'Components: main' \
  'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
  '' \
  'Types: deb' \
  'URIs: http://mirrors.edge.kernel.org/debian-security' \
  'Suites: bookworm-security' \
  'Components: main' \
  'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
  > /etc/apt/sources.list.d/debian.sources
  

# Run update and install system packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        libsndfile1 \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
