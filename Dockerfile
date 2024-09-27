# Dockerfile for Django with Python 3.12
FROM python:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/code
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update


# Install Python dependencies
COPY requirements.txt $APP_HOME/
RUN pip install --upgrade pip && \
pip install gunicorn && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . $APP_HOME/
# COPY entrypoint.sh $APP_HOME/
RUN chmod +x  $APP_HOME/entrypoint.sh

WORKDIR $APP_HOME/Ecommerce_API

ENTRYPOINT ["sh", "/code/entrypoint.sh"]