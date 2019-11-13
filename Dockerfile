FROM python:3.6-alpine

#RUN apt-get update -y && \
#    apt-get install -y python3-pip python3-dev
RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev openssl-dev postgresql-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 5001

ENTRYPOINT ["python3"]

CMD ["run.py", "docker"]