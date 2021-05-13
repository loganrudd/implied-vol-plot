FROM python:3.9-slim-buster as builder

WORKDIR /implied-vol-plot
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["bokeh", "serve", "--show", "iv_app.py"]