FROM python:3.7.2

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY app/ /app

CMD [ "python", "vaultexport.py" ]

