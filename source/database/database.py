from dataclasses import dataclass
from datetime import datetime

import pytz
from sqlalchemy import Engine, create_engine, desc
from sqlmodel import Session, SQLModel, select, text

from .model import (
    Associate,
    AssociateProductLink,
    Business,
    Conversation,
    Location,
    LocationProductLink,
    Message,
    Product,
    Schedule,
)


@dataclass
class PostgresCredentials:
    user: str
    password: str
    database: str
    host: str
    port: int


class DatabaseService:
    def __init__(self, credentials: PostgresCredentials) -> None:
        postgres_url = (
            f"postgresql://{credentials.user}:{credentials.password}@{credentials.host}:{credentials.port}"
            f"/{credentials.database}"
        )
        engine = create_engine(postgres_url)

        # create all sequences ahead of time
        with Session(engine) as session:
            stmt = text("CREATE SEQUENCE IF NOT EXISTS message_sequence START 1;")
            _ = session.execute(stmt)
            session.commit()

        SQLModel.metadata.create_all(engine)

        self.engine: Engine = engine

    def get_business_by_id(self, business_id: int) -> Business | None:
        with Session(self.engine) as session:
            stmt = select(Business).where(Business.id == business_id)
            business = session.exec(stmt).first()
        return business

    def create_conversation(self, business: Business, client_timezone: str, thread_id: str) -> Conversation:
        with Session(self.engine) as session:
            conversation = Conversation(business_id=business.id, client_timezone=client_timezone, thread_id=thread_id)
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
        return conversation

    def get_conversation_by_id(self, conversation_id: int) -> Conversation | None:
        with Session(self.engine) as session:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            conversation = session.exec(stmt).first()
        return conversation

    def insert_messages(self, messages: list[Message]) -> None:
        with Session(self.engine) as session:
            session.add_all(messages)
            session.commit()

            for message in messages:
                session.refresh(message)

    def get_associates_by_location_product(self, location_id: int, product_id: int) -> list[Associate]:
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
        with Session(self.engine) as session:
            stmt = select(Schedule).where(
                Schedule.associate_id == associate_id,
                Schedule.location_id == location_id,
                Schedule.start_datetime >= datetime.now(pytz.UTC),
            )
            results = session.exec(stmt).all()
            return list(results)

    def select_by_id(self, Table: type[SQLModel], id: int) -> list[SQLModel]:
        with Session(self.engine) as session:
            stmt = select(Table).where(Table.id == id).order_by(desc(Table.created_at))
            results = session.exec(stmt).all()
            return list(results)

    def get_associate_by_id(self, associate_id: int) -> Associate | None:
        with Session(self.engine) as session:
            associate_stmt = select(Associate).where(Associate.id == associate_id)
            associate = session.exec(associate_stmt).first()

        return associate

    def get_locations_by_product_id(self, product_id: int) -> list[Location]:
        with Session(self.engine) as session:
            stmt = select(Location).join(LocationProductLink).where(LocationProductLink.product_id == product_id)
            results = session.exec(stmt).all()
        return list(results)

    def get_products_by_assistant_id(self, assistant_id: str) -> list[Product]:
        with Session(self.engine) as session:
            stmt = select(Product).join(Business).where(Business.assistant_id == assistant_id)
            results = session.exec(stmt).all()
        return list(results)

    def get_associate_and_business_by_associate_id(self, associate_id: int) -> tuple[Associate | None, Business | None]:
        with Session(self.engine) as session:
            associate_stmt = select(Associate).where(Associate.id == associate_id)
            associate = session.exec(associate_stmt).first()

            business = None
            if associate:
                business_stmt = select(Business).where(Business.id == associate.business_id)
                business = session.exec(business_stmt).first()

        return associate, business

    def get_location_by_id(self, location_id: int) -> Location | None:
        with Session(self.engine) as session:
            stmt = select(Location).where(Location.id == location_id)
            location = session.exec(stmt).first()
        return location

    def get_all_associates(self) -> list[Associate]:
        with Session(self.engine) as session:
            stmt = select(Associate)
            associates = session.exec(stmt).all()
            return list(associates)

    def get_locations_by_associate_id(self, associate_id: int) -> list[Location]:
        with Session(self.engine) as session:
            stmt = (
                select(Location)
                .join(LocationProductLink, Location.id == LocationProductLink.location_id)
                .join(AssociateProductLink, LocationProductLink.product_id == AssociateProductLink.product_id)
                .where(AssociateProductLink.associate_id == associate_id)
            )
            results = session.exec(stmt).all()
        return list(results)
