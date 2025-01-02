from typing import TypedDict

from pydantic import BaseModel


class NotionPage(BaseModel):
    """Represents a Notion page with markdown content and possible child pages."""

    markdown: str
    children: list["NotionPage"]


class Annotation(TypedDict):
    """Describes text formatting annotations."""

    bold: bool | None
    italic: bool | None
    strikethrough: bool | None
    code: bool | None


class TextSegment(TypedDict):
    """Represents a segment of text with annotations."""

    annotations: Annotation
    plain_text: str


class RichText(TypedDict):
    """Contains a list of annotated text segments."""

    rich_text: list[TextSegment]


class TodoRichText(RichText):
    """Rich text used for to-do items, with an additional checked attribute."""

    checked: bool


class CodeRichText(RichText):
    """Rich text for code blocks, with an additional language attribute."""

    language: str


class Block(TypedDict):
    """Defines a block element with various types like paragraphs, headings, lists, etc."""

    type: str
    paragraph: RichText | None
    heading_1: RichText | None
    heading_2: RichText | None
    heading_3: RichText | None
    bulleted_list_item: RichText | None
    numbered_list_item: RichText | None
    to_do: TodoRichText | None
    code: CodeRichText

    # Children can contain other blocks or pages
    children: list["Block"] | None
    pages: list["Page"] | None


class Page(TypedDict):
    """Represents a page object with unique identifiers."""

    object: str
    id: str
