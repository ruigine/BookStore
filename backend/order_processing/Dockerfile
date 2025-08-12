FROM python:3-slim
WORKDIR /usr/src/app/order_processing
COPY order_processing/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY order_processing/ ./order_processing/
COPY shared/ ./shared/
ENV PYTHONPATH=/usr/src/app
CMD ["python", "-m", "order_processing.app"]