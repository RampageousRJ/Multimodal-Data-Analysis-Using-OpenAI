from fastmcp import FastMCP
from dotenv import load_dotenv
from openai_database import get_database_response
from openai_audio import transcribe_audio
from openai_image import caption_image
from openai_text import translate_text as lib_translate_text
from fastapi import Request
from fastapi.responses import JSONResponse

load_dotenv()

mcp = FastMCP("multimodal-openai-mcp", host="0.0.0.0", port=8000)  
# mcp = FastMCP("multimodal-openai-mcp")  

@mcp.tool
async def database_query_tool(path: str, question: str):
    """
    A tool to query a database using natural language questions.
    Args:
        path (str): The path to the database file.
        question (str): The question in natural language to query the database.
    Returns:
        dict: A dictionary containing the SQL query and the results of the query.
    """
    try:
        return get_database_response(path, question)
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

@mcp.tool
async def audio_query_tool(audio_path: str):
    """
    A tool to query an audio file using natural language questions.
    Args:
        audio_path (str): The path to the audio file.
    Returns:
        dict: A dictionary containing the results of the query.
    """
    try:
        return transcribe_audio(audio_path)
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

@mcp.tool
async def image_caption_tool(image_path: str):
    """
    A tool to query an image file using natural language questions.
    Args:
        image_path (str): The path to the image file.
    Returns:
        dict: A dictionary containing the results of the query.
    """
    try:
        return caption_image(image_path)
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

@mcp.tool
async def translate_text(text: str, language: str):
    """
    A tool to translate text using natural language questions.
    Args:
        text (str): The text to translate.
        language (str): The language to translate to.
    Returns:
        dict: A dictionary containing the results of the query.
    """
    try:
        return lib_translate_text(text, language)
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }


@mcp.custom_route("/rephrase_translate", methods=["POST"])
async def rephrase_translate(request: Request):
    data = await request.json()
    text = data.get("text")
    language = data.get("language")
    try:
        raw_result = await translate_text.fn(text, language)
        return JSONResponse(content={"result": raw_result}) 
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),    
                "type": type(e).__name__
            }
        )

if __name__ == "__main__":
    print("Starting the server...")
    mcp.run(transport="sse")