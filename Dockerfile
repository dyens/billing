FROM python:3.7.5
MAINTAINER Kapustin Alexander <dyens@mail.ru>

WORKDIR /opt/project

RUN pip install poetry==1.0.0b4
ADD poetry.lock /opt/project/

ADD pyproject.toml /opt/project/
RUN poetry install --no-dev -vvv
CMD exec make run
