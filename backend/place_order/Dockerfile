FROM python:3-slim
WORKDIR /usr/src/app/place_order
COPY place_order/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY place_order/ ./place_order/
COPY shared/ ./shared/
ENV PYTHONPATH=/usr/src/app
CMD ["python", "-m", "place_order.app"]