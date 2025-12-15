# Dockerfile for AWS Lambda (Python) with Playwright
# Alternative deployment method using container images

FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for Playwright
RUN yum install -y \
    wget \
    unzip \
    libX11 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXtst \
    cups-libs \
    libXScrnSaver \
    libXrandr \
    alsa-lib \
    pango \
    atk \
    at-spi2-atk \
    gtk3 \
    && yum clean all

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Install Playwright and browsers
RUN pip install playwright==1.40.0 && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY config/ ${LAMBDA_TASK_ROOT}/config/

# Set environment variables
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}:${PYTHONPATH}"
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Lambda handler
CMD ["src.lambda_handler.lambda_handler"]
