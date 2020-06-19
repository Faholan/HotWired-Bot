FROM python:3.8-slim

# Setting environment variables
ENV PIPENV_IGNORE_VIRTUALENVS=1 \
    PIPENV_VENV_IN_PROJECT=1

# Installing dependencies
RUN pip install --upgrade pip
RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv sync

# Copying all the files files over to the workdir
COPY . ./

# Running the container when asked with pipenv
ENTRYPOINT ["pipenv"]
CMD ["run", "start"]