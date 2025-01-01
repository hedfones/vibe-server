from dataclasses import dataclass
from datetime import datetime

import pytz
from sqlalchemy import Engine, create_engine, desc
from sqlmodel import Session, SQLModel, select, text

from .model import (
    Assistant,
    Associate,
    AssociateProductLink,
    Business,
    Conversation,
    Location,
    LocationProductLink,
    Message,
    Photo,
    PhotoProductLink,
    Product,
    Schedule,
)


@dataclass
class PostgresCredentials:
    """Data class that holds the credentials required to connect to a PostgreSQL database."""

    user: str
    password: str
    database: str
    host: str
    port: int


class DatabaseService:
    def __init__(self, credentials: PostgresCredentials) -> None:
        """Initialize the database connection using the provided credentials."""
        # Construct the PostgreSQL URL using the provided database credentials
        postgres_url = (
            f"postgresql://{credentials.user}:{credentials.password}@{credentials.host}:{credentials.port}"
            f"/{credentials.database}"
        )
        # Create an SQLAlchemy engine using the constructed PostgreSQL URL
        engine = create_engine(postgres_url)

        # Create all sequences ahead of time if they do not already exist
        with Session(engine) as session:
            stmt = text("CREATE SEQUENCE IF NOT EXISTS message_sequence START 1;")
            _ = session.execute(stmt)
            session.commit()

        # Create all tables defined in the SQLModel metadata
        SQLModel.metadata.create_all(engine)

        self.engine: Engine = engine

    def get_business_by_id(self, business_id: int) -> Business | None:
        """Retrieve a Business by its ID.

        Args:
            business_id (int): The ID of the business to retrieve.

        Returns:
            Business | None: The corresponding Business object if found; otherwise, None.
        """
        with Session(self.engine) as session:
            stmt = select(Business).where(Business.id == business_id)
            business = session.exec(stmt).first()
        return business

    def get_assistant_by_business_and_type(self, business_id: int, assistant_type: str) -> Assistant:
        with Session(self.engine) as session:
            stmt = select(Assistant).where(Assistant.business_id == business_id, Assistant.type == assistant_type)
            assistant = session.exec(stmt).one()
        return assistant

    def update_assistant_context(self, business_id: int, context: str) -> None:
        """Update the context of a business.

        Args:
            business_id (int): The ID of the business whose assistant context is to be updated.
            context (str): The new context to set for the assistant.
        """
        with Session(self.engine) as session:
            stmt = select(Assistant).where(Assistant.business_id == business_id)
            assistant = session.exec(stmt).first()
            if assistant:
                assistant.context = context
                session.add(assistant)
                session.commit()

    def create_conversation(self, business: Business, client_timezone: str, thread_id: str) -> Conversation:
        """Create a new conversation.

        Args:
            business (Business): The business associated with the conversation.
            client_timezone (str): The timezone of the client.
            thread_id (str): The thread ID of the conversation.

        Returns:
            Conversation: The newly created conversation object.
        """
        with Session(self.engine) as session:
            conversation = Conversation(business_id=business.id, client_timezone=client_timezone, thread_id=thread_id)
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
        return conversation

    def get_conversation_by_id(self, conversation_id: int) -> Conversation | None:
        """Retrieve a conversation by its ID.

        Args:
            conversation_id (int): The ID of the conversation to retrieve.

        Returns:
            Conversation | None: The corresponding Conversation object if found; otherwise, None.
        """
        with Session(self.engine) as session:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            conversation = session.exec(stmt).first()
        return conversation

    def insert_messages(self, messages: list[Message]) -> None:
        """Insert multiple messages into the database.

        Args:
            messages (list[Message]): A list of Message objects to be inserted.
        """
        with Session(self.engine) as session:
            session.add_all(messages)
            session.commit()

            # Refresh each message to ensure the latest state from the database
            for message in messages:
                session.refresh(message)

    def get_associates_by_location_product(self, location_id: int, product_id: int) -> list[Associate]:
        """Retrieve associates associated with a specific location and product.

        Args:
            location_id (int): The ID of the location.
            product_id (int): The ID of the product.

        Returns:
            list[Associate]: A list of Associate objects associated with the specified location and product.
        """
        with Session(self.engine) as session:
            stmt = (
                select(Associate)
                .join(
                    AssociateProductLink,
                    AssociateProductLink.associate_id == Associate.id,
                )
                .join(
                    LocationProductLink,
                    LocationProductLink.product_id == AssociateProductLink.product_id,
                )
                .where(
                    LocationProductLink.location_id == location_id,
                    AssociateProductLink.product_id == product_id,
                )
            )
            associates = session.exec(stmt).all()

            return list(associates)

    def get_going_forward_schedules_by_location_associate(self, location_id: int, associate_id: int) -> list[Schedule]:
        """Retrieve schedules for a location and associate starting from the current time forward.

        Args:
            location_id (int): The ID of the location.
            associate_id (int): The ID of the associate.

        Returns:
            list[Schedule]: A list of Schedule objects for the specified location and associate that start from the current time or later.
        """
        with Session(self.engine) as session:
            stmt = select(Schedule).where(
                Schedule.associate_id == associate_id,
                Schedule.location_id == location_id,
                Schedule.start_datetime >= datetime.now(pytz.UTC),
            )
            results = session.exec(stmt).all()
            return list(results)

    def select_by_id(self, Table: type[SQLModel], id: int) -> list[SQLModel]:
        """Retrieve records from a table by ID, ordered by creation time.

        Args:
            Table (type[SQLModel]): The table from which to select.
            id (int): The ID by which to filter the records.

        Returns:
            list[SQLModel]: A list of model objects from the specified table ordered by creation time.
        """
        with Session(self.engine) as session:
            stmt = select(Table).where(Table.id == id).order_by(desc(Table.created_at))
            results = session.exec(stmt).all()
            return list(results)

    def get_associate_by_id(self, associate_id: int) -> Associate | None:
        """Retrieve an associate by ID.

        Args:
            associate_id (int): The ID of the associate to retrieve.

        Returns:
            Associate | None: The corresponding Associate object if found; otherwise, None.
        """
        with Session(self.engine) as session:
            associate_stmt = select(Associate).where(Associate.id == associate_id)
            associate = session.exec(associate_stmt).first()

        return associate

    def get_locations_by_product_id(self, product_id: int) -> list[Location]:
        """Retrieve locations associated with a specific product.

        Args:
            product_id (int): The ID of the product.

        Returns:
            list[Location]: A list of Location objects associated with the specified product.
        """
        with Session(self.engine) as session:
            stmt = select(Location).join(LocationProductLink).where(LocationProductLink.product_id == product_id)
            results = session.exec(stmt).all()
        return list(results)

    def get_products_by_assistant_id(self, assistant_id: str) -> list[Product]:
        """Retrieve products associated with a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant.

        Returns:
            list[Product]: A list of Product objects associated with the specified assistant.
        """
        with Session(self.engine) as session:
            stmt = (
                select(Product)
                .join(Assistant, Assistant.business_id == Product.business_id)
                .where(Assistant.openai_assistant_id == assistant_id)
            )
            results = session.exec(stmt).all()
        return list(results)

    def get_associate_and_business_by_associate_id(self, associate_id: int) -> tuple[Associate | None, Business | None]:
        """Retrieve an associate and their business by the associate's ID.

        Args:
            associate_id (int): The ID of the associate.

        Returns:
            tuple[Associate | None, Business | None]: A tuple containing the corresponding Associate and Business objects if found;
                                                      otherwise, a tuple of None for associate and business.
        """
        with Session(self.engine) as session:
            associate_stmt = select(Associate).where(Associate.id == associate_id)
            associate = session.exec(associate_stmt).first()

            business = None
            if associate:
                business_stmt = select(Business).where(Business.id == associate.business_id)
                business = session.exec(business_stmt).first()

        return associate, business

    def get_location_by_id(self, location_id: int) -> Location | None:
        """Retrieve a location by its ID.

        Args:
            location_id (int): The ID of the location to retrieve.

        Returns:
            Location | None: The corresponding Location object if found; otherwise, None.
        """
        with Session(self.engine) as session:
            stmt = select(Location).where(Location.id == location_id)
            location = session.exec(stmt).first()
        return location

    def get_photos_by_product_id(self, product_id: int) -> list[Photo]:
        """Retrieve photos associated with a specific product.

        Args:
            product_id (int): The ID of the product.

        Returns:
            list[Photo]: A list of Photo objects associated with the specified product.
        """
        with Session(self.engine) as session:
            stmt = select(Photo).join(PhotoProductLink).where(PhotoProductLink.product_id == product_id)
            results = session.exec(stmt).all()
        return list(results)

    def get_photo_by_id(self, product_id: int) -> Photo | None:
        """Retrieve a photo by its ID.

        Args:
            product_id (int): The ID of the photo to retrieve.

        Returns:
            Photo | None: The corresponding Photo object if found; otherwise, None.
        """
        with Session(self.engine) as session:
            stmt = select(Photo).where(Photo.id == product_id)
            photo = session.exec(stmt).first()
        return photo

    def get_all_associates(self) -> list[Associate]:
        """Retrieve all associates.

        Returns:
            list[Associate]: A list of all Associate objects.
        """
        with Session(self.engine) as session:
            stmt = select(Associate)
            associates = session.exec(stmt).all()
            return list(associates)

    def get_locations_by_associate_id(self, associate_id: int) -> list[Location]:
        """Retrieve locations associated with a specific associate.

        Args:
            associate_id (int): The ID of the associate.

        Returns:
            list[Location]: A list of Location objects associated with the specified associate.
        """
        with Session(self.engine) as session:
            stmt = (
                select(Location)
                .join(LocationProductLink, Location.id == LocationProductLink.location_id)
                .join(AssociateProductLink, LocationProductLink.product_id == AssociateProductLink.product_id)
                .where(AssociateProductLink.associate_id == associate_id)
            )
            results = session.exec(stmt).all()
        return list(results)

    def update_business(self, business_id: int, updates: dict[str, str | int | float | bool | None]) -> None:
        """Update business fields.

        Args:
            business_id (int): The ID of the business to update
            updates (dict[str, str]): Dictionary of field names and values to update
        """
        with Session(self.engine) as session:
            business = session.get(Business, business_id)
            if business:
                for key, value in updates.items():
                    setattr(business, key, value)
                session.add(business)
                session.commit()

    def get_first_associate_timezone_by_business_id(self, business_id: int) -> str:
        """Retrieve the timezone of the first associate of a business.

        Args:
            business_id (int): The ID of the business.

        Returns:
            str: The timezone of the first associate if found; otherwise, None.
        """
        with Session(self.engine) as session:
            stmt = select(Associate).where(Associate.business_id == business_id)
            associate = session.exec(stmt).first()
            assert associate is not None
        return associate.timezone  # Assuming the Associate model has a timezone attribute

    def get_all_assistants_by_business_id(self, business_id: int) -> list[Assistant]:
        """Retrieve all assistants associated with a specific business.

        Args:
            business_id (int): The ID of the business.

        Returns:
            list[Assistant]: A list of Assistant objects associated with the specified business.
        """
        with Session(self.engine) as session:
            stmt = select(Assistant).where(Assistant.business_id == business_id)
            assistants = session.exec(stmt).all()
        return list(assistants)
