from fastapi import FastAPI

from app.dependencies import lifespan
from app.routers import beers, breweries, reviews

app = FastAPI(lifespan=lifespan)

app.include_router(beers.router)
app.include_router(breweries.router)
app.include_router(reviews.router)
