FROM python:3.9-buster

RUN pip install -U pip

RUN adduser --disabled-password --gecos '' thor
RUN mkdir /opt/frontend && \
    chown -R thor:thor /opt/frontend

WORKDIR /opt/frontend
USER thor

COPY --chown=thor:thor ./requirements.txt requirements.txt
ENV VIRTUAL_ENV=/opt/frontend/venv

RUN python -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"
RUN pip install -r requirements.txt

COPY --chown=thor:thor ./src src

ENV FLASK_APP=src/app

CMD flask run
