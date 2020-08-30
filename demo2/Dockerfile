# FROM tensorflow/serving:latest
FROM tensorflow/serving:latest-devel

ENV MODEL_BASE_PATH=/models
ENV MODEL_NAME=cats_vs_dogs
COPY saved_model_dir /models/cats_vs_dogs/1

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Copy application dependency manifests to the container image.
# Copying this separately prevents re-running pip install on every code change.
COPY requirements.txt ./

# Install production dependencies.
RUN pip install -r requirements.txt

COPY tf_serving_entrypoint.sh tf_serving_entrypoint.sh
COPY gunicorn_entrypoint.sh gunicorn_entrypoint.sh
COPY wrapper_script.sh wrapper_script.sh

COPY main.py main.py
# CMD ./tf_serving_entrypoint.sh
# CMD ./gunicorn_entrypoint.sh
CMD ./wrapper_script.sh
