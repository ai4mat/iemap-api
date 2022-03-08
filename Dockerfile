FROM python:3.9.5-slim

COPY requirements.txt /
RUN python3 -m pip install --upgrade pip
RUN pip3 install -r /requirements.txt

WORKDIR /app
COPY /app /app

EXPOSE 8000

CMD ["python", "main.py"]

