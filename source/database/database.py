from dataclasses import dataclass
from typing import List

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select, text

from .model import Business, Conversation, Message


@dataclass
class PostgresCredentials:
    user: str
    password: str
    database: str = "database"
    host: str = "localhost"
    port: int = 5432


class DatabaseService:
    def __init__(self, credentials: PostgresCredentials) -> None:
        postgres_url = f"postgresql://{credentials.user}:{credentials.password}@{credentials.host}:{credentials.port}/{credentials.database}"
        engine = create_engine(postgres_url)

        # create all sequences ahead of time
        with Session(engine) as session:
            stmt = text("CREATE SEQUENCE IF NOT EXISTS message_sequence START 1;")
            session.execute(stmt)
            session.commit()

        SQLModel.metadata.create_all(engine)

        self.engine = engine

    def get_business_by_id(self, business_id: int) -> Business | None:
        with Session(self.engine) as session:
            stmt = select(Business).where(Business.id == business_id)
            business = session.exec(stmt).first()
        return business

    def create_conversation(self, business: Business, thread_id: str) -> Conversation:
        with Session(self.engine) as session:
            conversation = Conversation(business_id=business.id, thread_id=thread_id)
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
        return conversation

    def get_conversation_by_id(self, conversation_id: int) -> Conversation | None:
        with Session(self.engine) as session:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            conversation = session.exec(stmt).first()
        return conversation

    def insert_messages(self, messages: List[Message]) -> None:
        with Session(self.engine) as session:
            session.add_all(messages)
            session.commit()
