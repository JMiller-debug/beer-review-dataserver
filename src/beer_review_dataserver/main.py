import uvicorn
from fastapi import FastAPI

from beer_review_dataserver.config import get_settings
from beer_review_dataserver.dependencies import lifespan
from beer_review_dataserver.routers import beers, breweries, reviews

app = FastAPI(lifespan=lifespan)

app.include_router(beers.router)
app.include_router(breweries.router)
app.include_router(reviews.router)


def main():
    settings = get_settings()
    uvicorn.run(
        "beer_review_dataserver.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=True,
    )


if __name__ == "__main__":
    main()
