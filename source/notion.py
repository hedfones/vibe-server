from typing import Any

from notion_client import Client

from .model import NotionPage


class NotionService:
    def __init__(self, auth_token: str):
        """Initialize the Notion service with an authentication token."""
        self.client: Client = Client(auth=auth_token)

    def get_page_content(self, page_id: str) -> list[NotionPage]:
        """Get the content of a Notion page and its children as markdown."""
        # Remove any dashes from the page ID if present
        page_id = page_id.replace("-", "")
        # Get all blocks for the page
        blocks = self.get_all_blocks(page_id)
        # Convert blocks to NotionPage and markdown
        pages = self._blocks_to_notion_pages(blocks)
        return pages  # Returning the list of NotionPage instead of markdown

    def get_all_blocks(self, block_id: str, processed: set[str] | None = None) -> list[dict[str, Any]]:
        """Recursively get all blocks for a page, including nested blocks and databases."""
        if processed is None:
            processed = set()

        blocks = []

        # Get the initial blocks
        response = self.client.blocks.children.list(block_id)
        blocks.extend(response["results"])
        processed.add(block_id)

        # Continue paginating if there are more blocks
        while response.get("has_more", False):
            response = self.client.blocks.children.list(block_id, start_cursor=response["next_cursor"])
            blocks.extend(response["results"])

        # Recursively get child blocks
        for block in blocks:
            block_id = block["id"]
            if block_id in processed:
                continue

            if block["has_children"]:
                child_blocks = self.get_all_blocks(block_id, processed)
                block["children"] = child_blocks

        return blocks

    def _blocks_to_notion_pages(self, blocks: list[dict[str, Any]]) -> list[NotionPage]:
        """Convert Notion blocks to NotionPage objects."""
        notion_pages: list[NotionPage] = []

        for block in blocks:
            page = NotionPage(markdown="", children=[])  # Initialize with empty markdown and children

            block_type: str = block["type"]

            # Generate markdown content
            if block_type == "paragraph":
                page.markdown = self._get_rich_text(block["paragraph"]["rich_text"])

            elif block_type == "heading_1":
                page.markdown = f"# {self._get_rich_text(block['heading_1']['rich_text'])}"

            elif block_type == "heading_2":
                page.markdown = f"## {self._get_rich_text(block['heading_2']['rich_text'])}"

            elif block_type == "heading_3":
                page.markdown = f"### {self._get_rich_text(block['heading_3']['rich_text'])}"

            elif block_type == "bulleted_list_item":
                page.markdown = f"- {self._get_rich_text(block['bulleted_list_item']['rich_text'])}"

            elif block_type == "numbered_list_item":
                page.markdown = f"1. {self._get_rich_text(block['numbered_list_item']['rich_text'])}"

            elif block_type == "to_do":
                text = self._get_rich_text(block["to_do"]["rich_text"])
                checked: bool = block["to_do"]["checked"]
                checkbox = "[x]" if checked else "[ ]"
                page.markdown = f"{checkbox} {text}"

            elif block_type == "code":
                text = self._get_rich_text(block["code"]["rich_text"])
                language: str = block["code"].get("language", "")
                page.markdown = f"```{language}\n{text}\n```"

            elif block_type == "quote":
                page.markdown = f"> {self._get_rich_text(block['quote']['rich_text'])}"

            elif block_type == "divider":
                page.markdown = "---"

            # Handle child blocks recursively and add to NotionPage children
            if block.get("has_children") and "children" in block:
                child_pages = self._blocks_to_notion_pages(block["children"])
                page.children.extend(child_pages)

            notion_pages.append(page)

        return notion_pages

    def _get_rich_text(self, rich_text: list[dict[str, Any]]) -> str:
        """Extract text content from rich text objects."""
        if not rich_text:
            return ""

        text_parts = []
        for text in rich_text:
            content = text["plain_text"]

            # Apply basic formatting
            if text.get("annotations"):
                if text["annotations"].get("bold"):
                    content = f"**{content}**"
                if text["annotations"].get("italic"):
                    content = f"*{content}*"
                if text["annotations"].get("strikethrough"):
                    content = f"~~{content}~~"
                if text["annotations"].get("code"):
                    content = f"`{content}`"

            text_parts.append(content)

        return "".join(text_parts)
