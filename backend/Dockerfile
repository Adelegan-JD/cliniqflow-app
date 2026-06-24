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
# #     && rm -rf /var/lib/apt/lists/*

# # RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources

# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         build-essential \
#     && rm -rf /var/lib/apt/lists/*



# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8000

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN printf '%s\n' \
  'Types: deb' \
  'URIs: https://cloudflaremirrors.com/debian' \
  'Suites: bookworm bookworm-updates' \
  'Components: main' \
  'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
  '' \
  'Types: deb' \
  'URIs: https://cloudflaremirrors.com/debian-security' \
  'Suites: bookworm-security' \
  'Components: main' \
  'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
  > /etc/apt/sources.list.d/debian.sources
  
# Run update and install backend system packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
