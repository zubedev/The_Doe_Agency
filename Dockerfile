FROM python:3.9-slim
MAINTAINER ziibii88

ENV PYTHONUNBUFFERED 1

RUN apt update -y
# install build tools; for example: psycopg2 dev tools
RUN apt install -y gcc curl build-essential python3-dev libpq-dev wget gnupg

# Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt update -y && apt install -y google-chrome-stable

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
