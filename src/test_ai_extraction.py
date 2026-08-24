import base64
from pathlib import Path

from openai import OpenAI


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

INPUT_DIR = Path("data/raw")
OUTPUT_DIR = Path("output/json")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

client = OpenAI()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def encode_image(image_path):

    with open(image_path, "rb") as f:
        return base64.b64encode(
            f.read()
        ).decode("utf-8")


# ------------------------------------------------------------------
# Extraction
# ------------------------------------------------------------------

def extract_sheet(image_path):

    print(
        f"
Processing {image_path.name}"
    )

    image_b64 = encode_image(
        image_path
    )

    prompt = """
This is a sailing race scoresheet.

Extract ALL competitor entries visible on the sheet.

Return JSON ONLY.

For each competitor return:

- class
- sail_number
- helm_crew

Rules:

- Do not invent information.
- Preserve names exactly as written.
- Preserve sail numbers exactly as written.
- If a value cannot be read use null.
- Include every visible competitor row.
- Ignore race results.
- Ignore lap times.
- Ignore finishing positions.

Return a JSON array only.

Example:

[
  {
    "class": "Comet",
    "sail_number": "437",
    "helm_crew": "Pete Chambers"
  },
  {
    "class": "SIN",
    "sail_number": "1320",
    "helm_crew": "Phil Watson"
  }
]
"""

    response = client.responses.create(
        model="gpt-5",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}"
                    }
                ]
            }
        ]
    )

    result = response.output_text

    output_file = (
        OUTPUT_DIR /
        f"{image_path.stem}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(result)

    print(
        f"Saved {output_file}"
    )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    files = []

    files.extend(
        INPUT_DIR.glob("*.jpg")
    )

    files.extend(
        INPUT_DIR.glob("*.jpeg")
    )

    files.extend(
        INPUT_DIR.glob("*.png")
    )

    print(
        f"Found {len(files)} images"
    )

    if len(files) == 0:
        print("No images found.")
        return

    # Start with just one sheet
    extract_sheet(files[0])


if __name__ == "__main__":
    main()
