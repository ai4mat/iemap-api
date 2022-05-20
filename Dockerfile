FROM python:3.9.5-slim

COPY requirements.txt /
RUN apt-get update && apt-get -y install gcc
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir -r /requirements.txt

COPY /app /app
WORKDIR /app

EXPOSE 80

CMD python -m uvicorn main:app --host 0.0.0.0 --port 80