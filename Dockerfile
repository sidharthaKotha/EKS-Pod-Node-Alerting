ROM python:3.7-alpine

RUN mkdir /app
WORKDIR /app
COPY ./async.py /app/
ADD ./requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["python3", "/app/async.py"]
