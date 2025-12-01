# Beer Review Dataserver

This repo is currently used to act as the REST API interface for the Beer Review
Website

This is just part of a side project that I am working on to learn a couple new
technologies, mainly SQLModel, Next.js and Alembic.


## Current State

There are 3 different models being used at the moment:
- Beers: Contains the individual beer and its rating score. Linked to a company
  and has reviews linked to it
- Breweries: Contains the Company that each beer is linked to.
- Reviews: Contains the reviews linked to each beer

All of these are contained in a postgresql database running out of docker.

## Routes

Each model has its own route that is used to interact with the database. Refer
to the /docs link when running the dataserver.


## Installation
### Virtual Env Creation

First create your virtual environment and source it as follows
```bash
$ uv venv --seed --prompt dataserver
$ source venv/bin/activate # Linux
$ ./venv/Scripts/activate.ps1 # Windows
```

### User

If you have cloned the repo, simply 
```bash
$ uv pip install . 
```
to install the package. This should include all the requirements for running the
server.
### Developer

If you want to perform an editable install and include developer tools (Just
ruff at this point):
```bash
$ uv pip install -e . --group dev
```

## Running the dataserver

Once you have installed the dataserver and sourced the virtual environment, you
can now run the dataserver.

### Environment variables

The following environment variables are supplied to customise the dataserver and
are case insensitive:

- host: Default = 0.0.0.0 (All interfaces)
- port: Default = 8000
- log_level: Default = info 
  - Options: info | debug | error | critical | warning | none
- postgres_uri: Default =
  postgresql+asyncpg://postgres:postgres@localhost:5432/beer_review

### Starting the dataserver

Run the following to start the dataserver:
```bash
$ beer_dataserver
```

It should now be running. You can check out the default openApi docs on
[localhost:8000/docs](localhost:8000/docs)
