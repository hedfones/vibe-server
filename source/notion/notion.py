import structlog
from notion_client import Client

from .model import Block, NotionPage, Page, TextSegment

log = structlog.stdlib.get_logger()


class NotionService:
    def __init__(self, auth_token: str):
        """Initialize the Notion service with an authentication token."""
        self.client: Client = Client(auth=auth_token)
        log.info("NotionService initialized", auth_token=f"{auth_token[:10]}...")

    def get_page_content(self, page_id: str) -> NotionPage:
        """Get the content of a Notion page and its children, including databases, as NotionPage.

        Args:
            page_id (str): The ID of the Notion page to fetch the content for.

        Returns:
            NotionPage: An object containing the markdown content and children.
        """
        logger = log.bind(page_id=page_id)
        logger.info("Fetching page content")
        # Remove any dashes from the page ID if present
        page_id = page_id.replace("-", "")
        # Get all blocks for the page
        blocks = self.get_all_blocks(page_id)
        # Convert blocks to NotionPage
        page = self._blocks_to_notion_page(blocks)
        logger.info("Page content fetched successfully.")
        return page  # Returning the NotionPage

    def get_all_blocks(self, block_id: str, processed: set[str] | None = None) -> list[Block]:
        """Recursively get all blocks for a page, including nested blocks and databases.

        Args:
            block_id (str): The ID of the block to fetch all children for.
            processed (set[str] | None): A set to keep track of processed block IDs to avoid duplication.

        Returns:
            list[Block]: A list of Block objects retrieved.
        """
        if not processed:
            processed = set()
        log.info("Fetching all blocks", block_id=block_id)

        blocks: list[Block] = []
        response = self.client.blocks.children.list(block_id)
        blocks.extend(response["results"])
        processed.add(block_id)

        # Continue paginating if there are more blocks
        while response.get("has_more", False):
            response = self.client.blocks.children.list(block_id, start_cursor=response["next_cursor"])
            blocks.extend(response["results"])

        # Recursively get child blocks
        for block in blocks:
            if block.get("type") == "child_database":
                log.info("Fetching pages from child database", database_id=block["id"])
                # If the block is a child database, retrieve its pages
                database_id = block["id"]
                database_pages = self.get_database_pages(database_id)
                block["pages"] = database_pages

            block_id = block["id"]
            if block_id in processed:
                log.debug("Block already processed, skipping", block_id=block_id)
                continue

            if block.get("has_children"):
                log.info("Fetching child blocks", block_id=block_id)
                child_blocks = self.get_all_blocks(block_id, processed)
                block["children"] = child_blocks

        log.info("Completed fetching all blocks", block_id=block_id, total_blocks=len(blocks))
        return blocks

    def get_database_pages(self, database_id: str) -> list[Page]:
        """Retrieve all pages from a database.

        Args:
            database_id (str): The ID of the database from which to fetch pages.

        Returns:
            list[Page]: A list of Page objects retrieved from the database.
        """
        log.info("Retrieving pages from database", database_id=database_id)
        pages: list[Page] = []
        response = self.client.databases.query(database_id)

        # Add first page of results
        pages.extend(response["results"])
        log.info("Initial page results count", count=len(pages))

        # Continue paginating if there are more pages
        while response.get("has_more", False):
            response = self.client.databases.query(database_id, start_cursor=response["next_cursor"])
            pages.extend(response["results"])

        log.info("Total pages retrieved from database", database_id=database_id, total_pages=len(pages))
        return pages

    def _blocks_to_markdown(self, blocks: list[Block]) -> tuple[list[str], list[NotionPage]]:
        """Convert Notion blocks and pages to NotionPage objects.

        Args:
            blocks (list[Block]): A list of Notion Block objects to convert.

        Returns:
            tuple[list[str], list[NotionPage]]: A tuple containing two lists:
            one with markdown strings and other with NotionPage objects as children.
        """
        markdown: list[str] = []
        children: list[NotionPage] = []

        for block in blocks:
            block_type: str = block["type"]

            # Generate markdown content for non-database blocks
            if block_type == "paragraph":
                markdown.append(self._get_rich_text(block["paragraph"]["rich_text"]))
                log.debug("Added paragraph to markdown.")

            elif block_type == "heading_1":
                markdown.append(f"# {self._get_rich_text(block['heading_1']['rich_text'])}")
                log.debug("Added heading 1 to markdown.")

            elif block_type == "heading_2":
                markdown.append(f"## {self._get_rich_text(block['heading_2']['rich_text'])}")
                log.debug("Added heading 2 to markdown.")

            elif block_type == "heading_3":
                markdown.append(f"### {self._get_rich_text(block['heading_3']['rich_text'])}")
                log.debug("Added heading 3 to markdown.")

            elif block_type == "bulleted_list_item":
                markdown.append(f"- {self._get_rich_text(block['bulleted_list_item']['rich_text'])}")
                log.debug("Added bulleted list item to markdown.")

            elif block_type == "numbered_list_item":
                markdown.append(f"1. {self._get_rich_text(block['numbered_list_item']['rich_text'])}")
                log.debug("Added numbered list item to markdown.")

            elif block_type == "to_do":
                text = self._get_rich_text(block["to_do"]["rich_text"])
                checked = block["to_do"]["checked"]
                checkbox = "[x]" if checked else "[ ]"
                markdown.append(f"{checkbox} {text}")
                log.debug("Added to-do item to markdown.")

            elif block_type == "code":
                text = self._get_rich_text(block["code"]["rich_text"])
                language: str = block["code"].get("language", "")
                markdown.append(f"```{language}\n{text}\n```")
                log.debug("Added code block to markdown.")

            elif block_type == "quote":
                markdown.append(f"> {self._get_rich_text(block['quote']['rich_text'])}")
                log.debug("Added quote to markdown.")

            elif block_type == "divider":
                markdown.append("---")
                log.debug("Added divider to markdown.")

            # Handle child blocks recursively and add to NotionPage children
            if block.get("has_children") and "children" in block:
                child_markdown, _ = self._blocks_to_markdown(block["children"])
                child_markdown = [f"\t{md}" for md in child_markdown]
                markdown.extend(child_markdown)

            if pages := block.get("pages"):
                for page_ref in pages:
                    log.info("Fetching content for page reference", page_ref_id=page_ref["id"])
                    notion_page = self.get_page_content(page_ref["id"])
                    children.append(notion_page)

        return markdown, children

    def _blocks_to_notion_page(self, blocks: list[Block]) -> NotionPage:
        """Convert a list of Notion blocks to a NotionPage object.

        Args:
            blocks (list[Block]): A list of Notion Block objects.

        Returns:
            NotionPage: A NotionPage object containing the markdown and children.
        """
        markdown, children = self._blocks_to_markdown(blocks)
        md_string = "\n\n".join(markdown)
        page = NotionPage(markdown=md_string, children=children)
        log.info("NotionPage created with markdown content.")
        return page

    def _get_rich_text(self, rich_text: list[TextSegment]) -> str:
        """Extract text content from rich text objects.

        Args:
            rich_text (list[TextSegment]): A list of rich text segment objects to extract from.

        Returns:
            str: The combined text extracted from the rich text segments.
        """
        if not rich_text:
            log.warning("Received empty rich text.")
            return ""

        text_parts: list[str] = []
        for text in rich_text:
            content = text["plain_text"]

            # Apply some basic formatting
            if text.get("annotations"):
                if text["annotations"].get("bold"):
                    content = f"**{content}**"
                if text["annotations"].get("italic"):
                    content = f"*{content}*"
                if text["annotations"].get("strikethrough"):
                    content = f"~~{content}~~"
                if text["annotations"].get("code"):
                    content = f"`{content}`"

            log.debug("Extracted rich text content", content=content)
            text_parts.append(content)

        return "".join(text_parts)
