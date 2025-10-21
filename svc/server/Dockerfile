FROM python:3.11-bullseye

WORKDIR /app

COPY . /app/

COPY ./requirements.txt /app/

RUN apt-get update

RUN python3 -m pip install -r requirements.txt

CMD [ "uvicorn" , "main:app", "--host", "0.0.0.0", "--port", "8081"]
