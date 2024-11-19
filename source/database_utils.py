from typing import List

from fastapi import HTTPException

from .database import DatabaseService, PostgresCredentials, Product
from .model import AvailabilityWindow
from .scheduler import Scheduler
from .secret_manager import SecretsManager

secrets = SecretsManager("./.env")

db_creds = PostgresCredentials(
    user=secrets.get("POSTGRES_USER"),
    password=secrets.get("POSTGRES_PASSWORD"),
    database=secrets.get("POSTGRES_DB"),
    host=secrets.get("POSTGRES_HOST"),
    port=secrets.get("POSTGRES_PORT"),
)
db = DatabaseService(db_creds)

scheduler = Scheduler(db)


def get_availability(product_id: int, location_id: int) -> List[AvailabilityWindow]:
    products: List[Product] = db.select_by_id(Product, product_id)
    product = products.pop(0)
    if not product:
        raise HTTPException(403, f"Unable to find product by id `{product_id}`")

    availabilities = scheduler.get_availabilities(
        product.id, product.duration_minutes, location_id
    )
    if not availabilities:
        raise HTTPException(
            403,
            "Unable to find availabilities associated with location "
            f"`{location_id}` and product `{product.id}`.",
        )

    return availabilities
