####################################################################################################
# Управление контейнерами с помощью docker-compose (dc)
####################################################################################################
dc-build: ## Сборка docker-образов согласно инструкциям из docker-compose.yml
	docker-compose -f _CI/docker-compose.yml build

dc-up-d: ## Создание и запуск docker-контейнеров, описанных в docker-compose.yml
	docker-compose -f _CI/docker-compose.yml up -d

dc-up: ## Создание и запуск docker-контейнеров, описанных в docker-compose.yml
	docker-compose -f _CI/docker-compose.yml up

dc-down: ## Остановка и УДАЛЕНИЕ docker-контейнеров, описанных в docker-compose.yml
	docker-compose -f _CI/docker-compose.yml down

dc-stop: ## Остановка docker-контейнеров, описанных в docker-compose.yml
	docker-compose -f _CI/docker-compose.yml stop

dc-start: ## Запуск docker-контейнеров, описанных в docker-compose.yml
	docker-compose -f _CI/docker-compose.yml start

dc-ps: ## Просмотр статуса docker-контейнеров, описанных в docker-compose.yml
	docker-compose -f _CI/docker-compose.yml ps

####################################################################################################
# Подключение к консоли контейнеров (контейнеры должны быть запущены)
####################################################################################################
console-psql: ## Подключение к консоли контейнера php-fmp (пользователь root)
	docker exec -it postgres bash

console-reader: ## Подключение к консоли контейнера php-fmp (пользователь root)
	docker exec -it reader bash

####################################################################################################
# Вспомогательные команды
####################################################################################################
clear-pg: ## Удаление данных базы Postgres
	sudo rm -R _CI/postgres/pg_data/
