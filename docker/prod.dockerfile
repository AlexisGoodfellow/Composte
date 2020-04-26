FROM alexisegoodfellow/composte:latest

WORKDIR /app

COPY . .

RUN pip install -r requirements.lock

EXPOSE 5000 5001

CMD [ "python", "composte/ComposteServer.py" ]
