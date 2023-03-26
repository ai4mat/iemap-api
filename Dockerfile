FROM python:3.9.5-slim

ARG UNAME=appuser
ARG UID=1000
ARG GID=1000


# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /

RUN apt-get update && apt-get -y install gcc && \
    python3 -m pip install --upgrade pip && \
    pip3 install --no-cache-dir -r /requirements.txt

COPY /app /app
WORKDIR /app

EXPOSE 80

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN bash -c 'if [[ ${ostype} == Linux ]] ; then addgroup --gid ${GID} ${UNAME} && \
    adduser --uid ${UID} --gid ${GID} --disabled-password --gecos "" ${UNAME} && \
    chown -R ${UID}:${GID} /app && \
    mkdir -p /data && \
    chown -R ${UID}:${GID} /data; fi'
USER ${UNAME}

CMD ["uvicorn", "main:app", "--proxy-headers", "--root-path", "/rest" ,"--host", "0.0.0.0", "--port", "80"]
