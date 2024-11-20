FROM python:3.8-slim 

WORKDIR /app

COPY app.py requirements.txt /app/

RUN pip install -r requirements.txt 

VOLUME /app/data

EXPOSE 5000 

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

