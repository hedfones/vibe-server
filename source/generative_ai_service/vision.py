import base64
import io
from pathlib import Path

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from PIL import Image

MAX_RESOLUTION = 3000  # pixels


def encode_image(image_path: str | Path) -> str:
    with Image.open(image_path) as img:
        if img.width > MAX_RESOLUTION or img.height > MAX_RESOLUTION:
            # Calculate new size while maintaining aspect ratio
            aspect_ratio = img.width / img.height
            new_width = 1500  # Desired width
            new_height = int(new_width / aspect_ratio)

            # Resize the image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save the image to a BytesIO object
        with io.BytesIO() as output:
            img.save(output, format="JPEG", quality=95)
            _ = output.seek(0)  # Move to the beginning of the BytesIO buffer
            return base64.b64encode(output.read()).decode("utf-8")


def describe_image(image_path: str | Path) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Please describe the provided image in a single sentence."),
            (
                "user",
                [
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            ),
        ]
    )

    chain = prompt | llm
    image_data = encode_image(image_path)
    response = chain.invoke({"base64_image": image_data})
    return response.content  # extract the response text from the response object
