from typing import TypedDict

from pydantic import BaseModel


class NotionPage(BaseModel):
    markdown: str
    children: list["NotionPage"]


class Annotation(TypedDict):
    bold: bool | None
    italic: bool | None
    strikethrough: bool | None
    code: bool | None


class TextSegment(TypedDict):
    annotations: Annotation
    plain_text: str


class RichText(TypedDict):
    rich_text: list[TextSegment]


class TodoRichText(RichText):
    checked: bool


class CodeRichText(RichText):
    language: str


class Block(TypedDict):
    type: str
    paragraph: RichText | None
    heading_1: RichText | None
    heading_2: RichText | None
    heading_3: RichText | None
    bulleted_list_item: RichText | None
    numbered_list_item: RichText | None
    to_do: TodoRichText | None
    code: CodeRichText

    children: list["Block"] | None
    pages: list["Page"] | None


class Page(TypedDict):
    object: str
    id: str
