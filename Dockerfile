FROM python:3.10-alpine

RUN apk update && apk --no-cache add build-base linux-headers python3-dev 

WORKDIR /app

COPY requirements.txt .

RUN pip install -U -r requirements.txt --no-cache-dir

COPY . .

ENTRYPOINT ["python", "main.py"]