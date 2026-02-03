# Partly copied from wonderwhy-er/DesktopCommanderMCP
# ? global dependency
FROM docker.1ms.run/library/node:lts-bullseye-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN sed -i 's|http://deb.debian.org/debian|http://mirrors.tuna.tsinghua.edu.cn/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://deb.debian.org/debian-security|http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list

# Install ca-certificates first to avoid GPG signature issues, then other packages
RUN apt-get update --allow-insecure-repositories && \
    apt-get install -y --fix-missing  --no-install-recommends --allow-unauthenticated ca-certificates && \
    update-ca-certificates && \
    apt-get install -y --no-install-recommends git bash curl wget unzip ripgrep vim sudo g++ locales

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# Install Chromium and dependencies

RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends \
        chromium \
        fonts-liberation \
        libappindicator3-1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        xdg-utils \
        fonts-dejavu \
        fonts-noto \
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        fonts-noto-color-emoji \
        fonts-freefont-ttf \
        fonts-urw-base35 \
        fonts-roboto \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        fonts-arphic-ukai \
        fonts-arphic-uming \
        fonts-ipafont \
        fonts-ipaexfont \
        fonts-comic-neue \
        imagemagick

# Create pptagent directory and install playwright
RUN mkdir -p /usr/src/pptagent/deeppresenter
WORKDIR /usr/src/pptagent
RUN npx playwright install chromium

# Copy deeppresenter code for installation
COPY . /usr/src/pptagent/deeppresenter/

# Install Node.js dependencies for html2pptx
WORKDIR /usr/src/pptagent/deeppresenter/deeppresenter/html2pptx
RUN npm install fast-glob minimist pptxgenjs playwright sharp
WORKDIR /usr/src/pptagent

# Set environment variables
ENV PATH="/opt/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV="/opt/.venv" \
    DEEPPRESENTER_WORKSPACE_BASE="/opt/workspace"

# Create Python virtual environment and install packages
RUN uv venv --python 3.13 $VIRTUAL_ENV && \
    uv pip install -e deeppresenter

# Install additional dependencies for API server
RUN uv pip install fastapi uvicorn sse-starlette httpx

# Install Playwright browsers for Python
RUN $VIRTUAL_ENV/bin/python -m playwright install chromium

# install libreoffice for pptx2image converting
RUN apt install -y libreoffice poppler-utils
RUN apt install -y docker.io

RUN fc-cache -f

# Copy startup script
COPY docker/start_services.sh /usr/src/pptagent/start_services.sh
RUN chmod +x /usr/src/pptagent/start_services.sh

# Expose API port
EXPOSE 4397

CMD ["bash", "-c", "/usr/src/pptagent/start_services.sh"]
