FROM python:3.12

EXPOSE 8080:8080

WORKDIR /wenote

COPY config.py main.py .env /wenote
COPY ./app /wenote/app

ENV FLASK_APP pybin.py
ENV REPO_PATH "/wenote-repo"

RUN mkdir -p logs

WORKDIR /
RUN mkdir -p /wenote-repo
WORKDIR /wenote-repo
RUN git init
RUN git config --global init.defaultBranch master
RUN touch haha.txt
RUN echo "123" > haha.txt
RUN git config --global user.email "you@example.com"
RUN git config --global user.name "you@example.com"
RUN git add .
RUN git commit -m "upd"

COPY ./requirements.txt /wenote/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /wenote/requirements.txt
RUN pip install gunicorn


WORKDIR /wenote
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8080"]
