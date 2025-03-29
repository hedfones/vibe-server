# This module handles syncing Notion content for a business.
import structlog
from fastapi import APIRouter, Depends, Header, HTTPException

from source import SecretsManager
from source.notion import NotionPage, NotionService
from source.utils import db

log = structlog.stdlib.get_logger()
router = APIRouter()


# Create a dependency to check the API key
def api_key_dependency(x_api_key: str = Header(...)):
    if not db.validate_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")


# Instantiate the Notion service using our secrets.
secrets = SecretsManager()
notion_service = NotionService(secrets.get("NOTION_AUTH_TOKEN"))


@router.post("/sync-notion/", response_model=dict, dependencies=[Depends(api_key_dependency)])
def sync_notion(x_api_key: str = Header(...)) -> dict:
    """
    Sync Notion content for a business.

    Retrieves a Notion page, converts it into markdown (including its child pages),
    updates the business’s assistant context, and returns the page content.
    """
    business = db.get_business_by_api_key(x_api_key)
    try:
        notion_page: NotionPage = notion_service.get_page_content(business.notion_page_id)

        def get_page_markdown(page: NotionPage) -> str:
            child_markdown = "\n---\n".join(get_page_markdown(child) for child in page.children)
            markdown = f"{page.markdown}\n---\n*Child Pages*:\n---\n{child_markdown}\n"
            return markdown

        pages = get_page_markdown(notion_page)
        db.update_assistant_context(business.id, pages)
        return {"markdown_content": notion_page}
    except Exception as e:
        log.error("Error syncing Notion content", business_id=business.id, exception=str(e))
        raise HTTPException(500, f"Error syncing Notion content: {str(e)}") from e
