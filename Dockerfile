FROM python:3.12

EXPOSE 80:80

WORKDIR /wenote

COPY ./requirements.txt /wenote/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /wenote/requirements.txt

COPY ./config.py /wenote
COPY ./app /wenote/app

RUN mkdir -p logs

CMD ["uvicorn", "app.main:app", "--port", "80"]
