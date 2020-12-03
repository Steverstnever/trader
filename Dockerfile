FROM python:3.8.6

WORKDIR /python_app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN python setup.py install

CMD [ "python", "./scripts/main.py" ]