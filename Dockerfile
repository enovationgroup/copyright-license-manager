FROM python:3.8-slim

RUN mkdir -p /app /work

COPY . /app

RUN cd /app; \
    pip install --no-cache-dir -r requirements.txt; \
    pip install -e .

WORKDIR /work

ENTRYPOINT [ "clmgr" ]
