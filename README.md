# Система автоматического реферирования документов

# Требование к системе:
-	ubuntu 18.04 и выше, на версии 16.04 не будет работать
-	python 3.6 и выше

# Выполнение необходимых для запуска команд:
- sudo apt-get update
-	sudo apt-get install memcached
-	sudo apt-get install python3-venv python3-pip
-	зайти в директорию с лабой
-	в этой директории
-	python3 -m venv venv
-	source venv/bin/activate
-	pip install -U pip
-	pip install wheel
-	pip install -r requirements.txt
-	python manage.py runserver
