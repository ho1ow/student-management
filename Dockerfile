FROM python:3.10-slim

WORKDIR /app
COPY . .

ENV FLASK_APP=app
ENV FLASK_ENV=development



RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
