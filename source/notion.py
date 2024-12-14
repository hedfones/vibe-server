from typing import Any

from notion_client import Client


class NotionService:
    def __init__(self, auth_token: str):
        """Initialize the Notion service with an authentication token."""
        self.client: Client = Client(auth=auth_token)

    def get_page_content(self, page_id: str) -> str:
        """Get the content of a Notion page and its children as markdown."""
        # Remove any dashes from the page ID if present
        page_id = page_id.replace("-", "")

        # Get all blocks for the page
        blocks = self.get_all_blocks(page_id)

        # Convert blocks to markdown
        markdown = self._blocks_to_markdown(blocks)

        return markdown

    def get_all_blocks(self, block_id: str) -> list[dict[str, Any]]:
        """Recursively get all blocks for a page, including nested blocks."""
        blocks = []

        # Get the initial blocks
        response = self.client.blocks.children.list(block_id)
        blocks.extend(response["results"])

        # Continue paginating if there are more blocks
        while response.get("has_more", False):
            response = self.client.blocks.children.list(block_id, start_cursor=response["next_cursor"])
            blocks.extend(response["results"])

        # Recursively get child blocks
        for block in blocks:
            if block["has_children"]:
                child_blocks = self.get_all_blocks(block["id"])
                block["children"] = child_blocks

        return blocks

    def _blocks_to_markdown(self, blocks: list[dict[str, Any]], level: int = 0) -> str:
        """Convert Notion blocks to markdown format."""
        markdown: list[str] = []

        for block in blocks:
            block_type: str = block["type"]

            if block_type == "paragraph":
                text = self._get_rich_text(block["paragraph"]["rich_text"])
                if text:
                    markdown.append(f"{text}\n")

            elif block_type == "heading_1":
                text = self._get_rich_text(block["heading_1"]["rich_text"])
                markdown.append(f"# {text}\n")

            elif block_type == "heading_2":
                text = self._get_rich_text(block["heading_2"]["rich_text"])
                markdown.append(f"## {text}\n")

            elif block_type == "heading_3":
                text = self._get_rich_text(block["heading_3"]["rich_text"])
                markdown.append(f"### {text}\n")

            elif block_type == "bulleted_list_item":
                text = self._get_rich_text(block["bulleted_list_item"]["rich_text"])
                markdown.append(f"{'  ' * level}- {text}\n")

            elif block_type == "numbered_list_item":
                text = self._get_rich_text(block["numbered_list_item"]["rich_text"])
                markdown.append(f"{'  ' * level}1. {text}\n")

            elif block_type == "to_do":
                text = self._get_rich_text(block["to_do"]["rich_text"])
                checked: bool = block["to_do"]["checked"]
                checkbox = "[x]" if checked else "[ ]"
                markdown.append(f"{'  ' * level}- {checkbox} {text}\n")

            elif block_type == "code":
                text = self._get_rich_text(block["code"]["rich_text"])
                language: str = block["code"].get("language", "")
                markdown.append(f"```{language}\n{text}\n```\n")

            elif block_type == "quote":
                text = self._get_rich_text(block["quote"]["rich_text"])
                markdown.append(f"> {text}\n")

            elif block_type == "divider":
                markdown.append("---\n")

            # Handle child blocks recursively
            if block.get("has_children") and "children" in block:
                child_markdown = self._blocks_to_markdown(block["children"], level + 1)
                markdown.append(child_markdown)

        return "\n".join(markdown)

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
