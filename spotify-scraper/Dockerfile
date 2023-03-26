FROM python:3.9-buster

RUN pip install -U pip

RUN adduser --disabled-password --gecos '' thor
RUN mkdir /opt/spotify-scraper && \
    chown -R thor:thor /opt/spotify-scraper

WORKDIR /opt/spotify-scraper
USER thor

ENV VIRTUAL_ENV=/opt/spotify-scraper/venv

RUN python -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

COPY --chown=thor:thor . .

RUN pip install .
