FROM python:3.8-slim

RUN mkdir /app

COPY . /app

RUN cd /app; \
    pip install --no-cache-dir -r requirements.txt; \
    pip install -e .

ENTRYPOINT [ "clmgr" ]
