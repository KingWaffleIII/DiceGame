# DiceGame

## Navigating the repo

`DiceGame` holds the Django project files such as the master routing file and the settings file.

`api` is a Django app that holds the models, serializers and views for the API, as well as the consumer for the websocket (where the main game logic is).

`app` is a Django app that serves the frontend. It holds the templates and static files.

I have used Django, Django Rest Framework and Django Channels (Websockets) to handle the backend. I have used vanilla HTML, CSS, JS and a CSS library called Bootstrap to handle the frontend. The game supports realtime online multiplayer due to the use of websockets. I have use SQL indirectly as the database through Django's ORM.
The frontend is separate in such a way that it can be easily replaced with a mobile app or a desktop app. I have chosen to represent the dice rolls with CSS and JS but this can be done in anyway due to the modular nature of the project.

<a href="https://streamable.com/0spi5o" target="_blank">Demo</a>

## Running the project

1. Install pip requirements in `requirements.txt` with `python -m pip install -r requirements.txt`.
2. Run `python manage.py migrate` to create the database.
3. Run `python manage.py runserver` to start the server.

![Specification](spec.png)
