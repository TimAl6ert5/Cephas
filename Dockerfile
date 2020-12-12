FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY LICENSE README.md CHANGELOG.md main.py ./
COPY ./cephas/*.py ./cephas/

CMD [ "python", "./main.py" ]