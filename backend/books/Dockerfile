FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
# COPY app.py model.py ./
COPY . /usr/src/app/books
RUN [ -f /usr/src/app/books/__init__.py ] || touch /usr/src/app/books/__init__.py
CMD [ "python", "-m", "books.app"]