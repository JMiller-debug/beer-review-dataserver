import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles

from beer_review_dataserver.config import get_settings
from beer_review_dataserver.dependencies import lifespan
from beer_review_dataserver.routers import beers, breweries, reviews
import os


app = FastAPI(lifespan=lifespan)

# Include routes to the endpoints we wish to use
app.include_router(beers.router)
app.include_router(breweries.router)
app.include_router(reviews.router)

# Mount the beer images for now to act as a CDN for the website when querying images
current_dir = os.path.dirname(__file__)
app.mount("/images", StaticFiles(directory=f"{current_dir}\\images"), name="images")

# Creting an unimplemented route such that there is documentation on the /docs link
router = APIRouter(
    prefix="/images",
    tags=["Images"],
    responses={
        404: {"Description": "Not Found"},
        403: {"Description": "Not Authorised"},
    },
)


@router.get(
    "/",
    summary="Image Directory",
    description="Serves static beer pictures. Any beer image file can be accessed via /images/{filename}.",
)
async def serve_images():
    """
    This endpoint serves static image files.
    Example: /images/photo.jpg
    """
    pass  # This won't be called due to StaticFiles handling the path


app.include_router(router)


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
