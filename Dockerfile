FROM python:3.9.5-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /
RUN apt-get update && apt-get -y install gcc
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir -r /requirements.txt

COPY /app /app
WORKDIR /app

EXPOSE 80

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

#CMD python -m uvicorn main:app --host 0.0.0.0 --port 80
CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]