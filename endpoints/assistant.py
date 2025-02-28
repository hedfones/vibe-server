# This module provides an endpoint to update the assistant configurations.
import json
from pathlib import Path

import structlog
import yaml
from fastapi import APIRouter, Depends, Header, HTTPException

from source.bedrock_assistant import BedrockAssistant
from source.database.model import Business
from source.utils import db

log = structlog.stdlib.get_logger()
router = APIRouter()


def api_key_dependency(x_api_key: str = Header(...)):
    if not db.validate_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")


# No need to explicitly manage AWS credentials
# AWS SDK will automatically pick them up from environment variables


@router.post("/update-assistant/", dependencies=[Depends(api_key_dependency)])
def update_assistant(x_api_key: str = Header(...)) -> dict:
    """
    Update assistant configurations for a business.

    Reads function mapping, builds function definitions, and updates the assistant’s configuration.
    """
    business: Business = db.get_business_by_api_key(x_api_key)
    assistant_configs = db.get_all_assistants_by_business_id(business.id)

    for asst_config in assistant_configs:
        # Initialize with AWS Bedrock instead of OpenAI
        assistant = BedrockAssistant(
            credentials=None,  # Will use AWS credentials from environment variables
            assistant_id=asst_config.openai_assistant_id,
            instructions=asst_config.instructions,
        )
        instructions = f"{asst_config.instructions}\n\n{'-' * 80}\n\n{asst_config.context}"
        assistant_name = f"Vibe - {asst_config.type} - {business.name}"

        assistant_fields: dict = asst_config.model_dump()

        function_dir = Path("resources/functions")
        try:
            with open(function_dir / "function_mapping.yaml", "r") as f:
                function_fields: dict = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise HTTPException(500, "Function mapping file not found.") from e
        except yaml.YAMLError as e:
            raise HTTPException(500, f"Error parsing function mapping file: {e}") from e

        function_definitions = []
        for key, filename in function_fields.items():
            do_use_function = assistant_fields.get(key, False)
            if not do_use_function:
                continue
            filepath = function_dir / filename
            try:
                with filepath.open("r") as f:
                    function_definition = json.load(f)
            except FileNotFoundError as e:
                raise HTTPException(500, f"Function definition file {filename} not found.") from e
            except json.JSONDecodeError as e:
                raise HTTPException(500, f"Error parsing function definition file {filename}: {e}") from e

            function_definitions.append(function_definition)

        assistant.update_assistant(instructions, assistant_name, asst_config.model, function_definitions)

    return {"message": "Assistant(s) updated successfully."}
