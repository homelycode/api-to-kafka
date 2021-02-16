FROM python:3

COPY *.py requirements.txt /pyapp/

WORKDIR /pyapp

RUN python3 -m pip install -r requirements.txt

ENTRYPOINT [ "/pyapp/scrape.py" ]