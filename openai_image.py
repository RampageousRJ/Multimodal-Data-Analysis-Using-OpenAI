import argparse
import os
import base64
import openai
from dotenv import load_dotenv
load_dotenv()

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

# Encode local image to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{data}"

# Ask a question about the image
def answer_from_image(image_data, question, is_url=False):
    prompt = f"Answer the question based on the image: {question}. Ensure the answer is concise, relevant, and limited to one sentence."
    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data}},
        ],
    }
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[message]
    )
    return response.choices[0].message.content

# Generate a caption for the image
def caption_image(image_data, is_url=False):
    prompt = "Describe the image in one concise sentence. Keep it crisp and sweet."
    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data}},
        ],
    }
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[message]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # Command-line interface
    parser = argparse.ArgumentParser(description="Analyze images via URL or local path.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-image_path", type=str, help="Path to the local image file.")
    group.add_argument("-image_url", type=str, help="URL of the image to analyze.")
    parser.add_argument("-question", type=str, help="Question to ask about the image.")
    args = parser.parse_args()

    # Prepare image data
    if args.image_path:
        image_data = encode_image_to_base64(args.image_path)
        is_url = False
    else:
        image_data = args.image_url
        is_url = True

    # Perform captioning or Q&A based on presence of question
    if not args.question:
        caption = caption_image(image_data, is_url=is_url)
        print("Caption:", caption)
    else:
        answer = answer_from_image(image_data, args.question, is_url=is_url)
        print("Answer:", answer)
