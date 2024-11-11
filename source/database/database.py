from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from .model import Business, Conversation


class DatabaseService:
    def __init__(self) -> None:
        engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(engine)

        self.engine = engine

    def get_business_by_id(self, business_id: int) -> Business:
        with Session(self.engine) as session:
            stmt = select(Business).where(Business.id == business_id)
            business = session.exec(stmt).first()
        return business

    def create_conversation(self, business: Business) -> Conversation:
        with Session(self.engine) as session:
            conversation = Conversation(business_id=business.id)
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
        return conversation
