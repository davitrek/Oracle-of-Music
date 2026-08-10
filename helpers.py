import db_operations
import spotify
from config import Config
from data_classes import WebImage
from models import Artist


# takes list of Spotify images and selects best one
def select_best_image(images: list[WebImage]) -> WebImage:
    best_image = None

    for img in images:
        if not best_image:
            best_image = img
            continue
        else:
            best_image = better_squarer_image(best_image, img)

    return best_image


# takes two Spotify images and selects squarer image
def better_squarer_image(img1: WebImage, img2: WebImage) -> WebImage:
    non_squareness1 = image_non_squareness(img1.height, img1.width)
    non_squareness2 = image_non_squareness(img2.height, img2.width)

    if non_squareness1 < non_squareness2:
        return img1
    elif non_squareness1 > non_squareness2:
        return img2

    # images are both same non-squareness, return one closer to 'ideal'
    # image size
    if abs(max(img1.height, img1.width) - Config.IDEAL_IMAGE_SIZE) < abs(
        max(img2.height, img2.width) - Config.IDEAL_IMAGE_SIZE
    ):
        return img1

    return img2


def image_non_squareness(height, width) -> float:
    return (height - width) / max(height, width)


def convert_spotify_image_to_class(spotify_image: dict) -> WebImage:
    return WebImage(
        url=spotify_image["url"],
        height=spotify_image["height"],
        width=spotify_image["width"],
    )


# equivalent to spotify.fetch_best_artist_image but takes Artist instead of
# spotify id
def fetch_best_artist_image(artist: Artist) -> WebImage | None:
    return spotify.fetch_best_artist_image(
        db_operations.get_artist_spotify_id(artist)
    )
