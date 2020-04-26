FROM composte:latest

COPY . .

RUN pip install -r requirements-test.txt -r requirements.txt

EXPOSE 5000 5001

CMD ["/bin/bash"]
# CMD [ "python", "./ComposteServer.py" ]
