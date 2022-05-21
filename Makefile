APP_NAME = mi-api
ENV_FILE = .env

.PHONY: all

all: build run

build: 
	@echo 'Buinding container...'
	@docker build -t $(APP_NAME) .

run: 
	@echo 'Run container with fs support...'
	@docker run --restart always --detach -p 8000:80/tcp -v $(FILESDIR):/$(FILESDIR) --env-file $(ENV_FILE) $(APP_NAME)

start:
	@echo 'Starting container...'
	@docker ps -a | grep $(APP_NAME) | awk '{print $$1}' | xargs docker start

stop:
	@echo 'Stopping container...'
	@docker ps | grep $(APP_NAME) | awk '{print $$1}' | xargs docker stop

kill:
	@echo 'Killing container...'
	@docker ps | grep $(APP_NAME) | awk '{print $$1}' | xargs docker rm -f

clean:
	@echo 'Killing (eventually) dead container(s)...'
	@docker ps -a | grep $(APP_NAME) | awk '{print $$1}' | xargs -r docker rm -f
	@echo 'Removing container image...'
	@docker images | grep $(APP_NAME) | awk '{print $$3}' | xargs docker rmi
