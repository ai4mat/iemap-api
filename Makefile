APP_NAME = iemap-api
TAG = latest
ENV_FILE = .env
HOST_PORT = 8000
uid = `id -u`
gid = `id -g`
uname = `id -un`


.PHONY: all

all: build run

renew: clean all

build: 
	@echo '🏗️	Buinding container...'
	@docker build --tag $(APP_NAME):$(TAG) --build-arg UID=$(uid) --build-arg GID=$(gid) --build-arg UNAME=$(uname) .

run: 
	@echo '🏁	Run container with fs support...'
	@docker run --user $(uid) --restart always --detach -p $(HOST_PORT):80/tcp -v $(HOST_FILESDIR):/data --env-file $(ENV_FILE) $(APP_NAME):$(TAG)

start:
	@echo '🎬	Starting container...'
	@docker ps -a | grep $(APP_NAME):$(TAG) | awk '{print $$1}' | xargs docker start

stop:
	@echo '✋🏻	Stopping container...'
	@docker ps | grep $(APP_NAME):$(TAG) | awk '{print $$1}' | xargs docker stop

kill:
	@echo '💀	Killing container...'
	@docker ps | grep $(APP_NAME):$(TAG) | awk '{print $$1}' | xargs docker rm -f

clean:
	@echo '🧹	Cleaning all: killing container, removing eventually dead containers and remove images...'
	@docker ps -a | grep $(APP_NAME) | awk '{print $$1}' | xargs -r docker rm -f
	@echo 'Removing container image...'
	@docker images | grep $(APP_NAME) | awk '{print $$3}' | xargs docker rmi
