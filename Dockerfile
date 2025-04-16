FROM python:3.11-slim-bookworm

RUN mkdir -p /app /work

COPY . /app

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt; \
    pip install --no-cache-dir -e .

WORKDIR /work

ENTRYPOINT [ "clmgr" ]
