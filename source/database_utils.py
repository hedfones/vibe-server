from fastapi import HTTPException

from .database import DatabaseService, PostgresCredentials, Product
from .model import AvailabilityWindow
from .scheduler import Scheduler
from .secret_manager import SecretsManager

secrets = SecretsManager("./.env")

db_creds = PostgresCredentials(
    user=secrets.get("POSTGRES_USER") or "",
    password=secrets.get("POSTGRES_PASSWORD") or "",
    database=secrets.get("POSTGRES_DB") or "",
    host=secrets.get("POSTGRES_HOST") or "",
    port=int(secrets.get("POSTGRES_PORT") or 6543),
)
db = DatabaseService(db_creds)

scheduler = Scheduler(db)


def get_availability(product_id: int, location_id: int) -> list[AvailabilityWindow]:
    products: list[Product] = db.select_by_id(Product, product_id)
    if not products:
        raise HTTPException(404, detail=f"Unable to find product by id `{product_id}`")
    product = products.pop(0)

    availabilities = scheduler.get_availabilities(
        product.id, product.duration_minutes, location_id
    )
    if not availabilities:
        raise HTTPException(
            404,
            detail="Unable to find availabilities associated with location "
            + f"`{location_id}` and product `{product.id}`.",
        )

    return availabilities


def get_product_locations(product_id: int) -> str:
    locations = db.get_locations_by_product_id(product_id)
    if not locations:
        raise HTTPException(
            404, f"Unable to find locations associated with product `{product_id}`."
        )

    location_string = "\n".join(map(str, locations))

    return location_string


def get_product_list(assistant_id: str) -> str:
    products = db.get_products_by_assistant_id(assistant_id)
    product_string = "\n".join(map(str, products))
    return product_string
