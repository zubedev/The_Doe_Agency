FROM python:3.9-slim
MAINTAINER ziibii88

ENV PYTHONUNBUFFERED 1

RUN apt update -y
# install build tools; for example: psycopg2 dev tools
RUN apt install -y gcc curl build-essential python3-dev libpq-dev

RUN python -m pip install --upgrade pip
# install poetry: https://python-poetry.org/docs/master/#installation
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
# add poetry to PATH environment
ENV PATH="/root/.local/bin:$PATH"

RUN mkdir /The_Doe_Agency
WORKDIR /The_Doe_Agency
COPY . /The_Doe_Agency
RUN mkdir -p logs && mkdir -p media && mkdir -p static

# install all dependencies via poetry
RUN poetry install
