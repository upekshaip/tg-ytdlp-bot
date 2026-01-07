FROM python:3.10-slim

ARG TZ=Europe/Moscow
ENV TZ="$TZ"

# System dependencies:
# - git, ffmpeg, mediainfo, rsync (README: base deps + FFmpeg)
# - font packages for Arabic/Asian and emoji support (README: optional fonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    mediainfo \
    rsync \
    fonts-noto-core \
    fonts-noto-extra \
    #fonts-kacst \
    fonts-kacst-one \
    fonts-noto-cjk \
    fonts-indic \
    fonts-noto-color-emoji \
    fontconfig \
    libass9 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Optional: install Amiri Arabic font (as in README)
RUN git clone https://github.com/aliftype/amiri.git /tmp/amiri \
    && mkdir -p /usr/share/fonts/truetype/amiri \
    && cp /tmp/amiri/fonts/*.ttf /usr/share/fonts/truetype/amiri/ \
    && fc-cache -fv \
    && rm -rf /tmp/amiri

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy and make the entrypoint executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

CMD ["/usr/local/bin/docker-entrypoint.sh"]
