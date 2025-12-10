import shutil
from pathlib import Path

import uvicorn
from fastapi import APIRouter, FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles

from beer_review_dataserver.config import get_settings
from beer_review_dataserver.dependencies import lifespan
from beer_review_dataserver.routers import beers, breweries, reviews

app = FastAPI(lifespan=lifespan)


# Include routes to the endpoints we wish to use
app.include_router(beers.router)
app.include_router(breweries.router)
app.include_router(reviews.router)

settings = get_settings()
# Mount the beer images for now to act as a CDN for the website when querying images
if settings.image_dir:
    image_dir = Path(settings.image_dir)
else:
    current_dir = Path(__file__).resolve().parent
    image_dir = current_dir / "images"

# Creting an unimplemented route such that there is documentation on the /docs link
router = APIRouter(
    prefix="/images",
    tags=["Images"],
    responses={
        404: {"Description": "Not Found"},
        403: {"Description": "Not Authorised"},
    },
)


@router.post("/")
async def post_image(beer_name: str, file: UploadFile | None = None):
    if not file:
        return {"message": "No upload file sent"}
    file_extension = Path(file.filename).suffix.lower()
    beer_name = beer_name.replace(" ", "-") + file_extension
    file_path = image_dir / beer_name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": beer_name}


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

# Need to mount after the router otherwise we can't post to this route
app.mount("/images", StaticFiles(directory=image_dir), name="images")


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
