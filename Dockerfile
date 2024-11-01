FROM python:3.12

EXPOSE 80:80

WORKDIR /wenote

COPY ./requirements.txt /wenote/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /wenote/requirements.txt

COPY ./config.py /wenote
COPY ./app /wenote/app

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

WORKDIR /wenote
CMD ["uvicorn", "app.main:app", "--port", "80", "--host", "0.0.0.0"]
