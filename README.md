# Multimodal Data Analysis Using OpenAI

## Project Description

The "Multimodal Data Analysis Using OpenAI" project provides a comprehensive framework for analyzing and processing text, audio, and image data via OpenAI's advanced models. It serves as a versatile toolset for executing complex data processing tasks including text analysis, audio transcription, and image interpretation with streamlined database interaction.

## Installation Instructions

1. Clone this repository:
   ```bash
   git clone https://github.com/RampageousRJ/Multimodal-Data-Analysis-Using-OpenAI.git
   ```
2. Navigate to the project directory.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Text Analysis**: Utilize `openai_text.py` for sentiment analysis of text or CSV files.
   ```bash
   # Analyze single text
   python openai_text.py -text "This is a great product!"

   # Analyze CSV file (must have 'text' column)
   python openai_text.py -path data/reviews.csv
   ```

2. **Audio Processing**: Leverage `openai_audio.py` to transcribe, translate, or analyze sentiment of audio files.
   ```bash
   # Transcribe audio
   python openai_audio.py -path data/audio.wav

   # Translate audio to target language
   python openai_audio.py -path data/audio.wav -translate Spanish

   # Analyze sentiment of audio content
   python openai_audio.py -path data/audio.wav -sentiment
   ```

3. **Image Analysis**: Use `openai_image.py` for captioning or answering questions about images.
   ```bash
   # Caption a local image
   python openai_image.py -image_path data/image.jpg

   # Answer a question about a local image
   python openai_image.py -image_path data/image.jpg -question "What color is the car?"

   # Analyze an image from URL
   python openai_image.py -image_url https://example.com/image.jpg
   ```

4. **Database Utilities**: Query a SQLite database using natural language with `openai_database.py`.
   ```bash
   python openai_database.py -path data/data.db -question "Show me all users from New York"
   ```

5. **MCP Server**: Run the Model Context Protocol server to expose these tools to an AI assistant.
   ```bash
   python main.py
   ```

## MCP Server Configuration

To use this tool as an MCP server with a client like **Claude Desktop**, you need to configure it in your `claude_desktop_config.json` file.

1.  **Locate or Create Config File**:
    -   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
    -   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2.  **Add Server Configuration**:
    Add the following entry to the `mcpServers` object. Replace `/ABSOLUTE/PATH/TO/PROJECT` with the actual absolute path to your cloned repository.

    ```json
    {
        "mcpServers": {
            "multimodal-openai-mcp": {
                "disabled": false,
                "timeout": 90,
                "type": "stdio",
                "command": "/ABSOLUTE/PATH/TO/uv",
                "args": [
                    "--directory",
                    "/ABSOLUTE/PATH/TO/PROJECT",
                    "run",
                    "main.py"
                ],
                "env": {
                    "VIRTUAL_ENV": "/ABSOLUTE/PATH/TO/PROJECT/.venv",
                    "PATH": "/ABSOLUTE/PATH/TO/PROJECT/.venv/bin:${PATH}"
                }
            }
        }
    }
    ```

    *Note: If you have a `.env` file in the project directory, the `env` block in the config might not be strictly necessary, but it's good practice to ensure the key is available to the server process.*

3.  **Restart Claude Desktop**:
    Completely quit and restart the Claude Desktop application to load the new server.

## Features

- **Multimodal Data Handling**: Comprehensive support for text, audio, and image data modalities.
- **OpenAI Integration**: Harnesses the power of OpenAI models for advanced data analysis.
- **Database Management**: Efficient data management and retrieval powered by robust database utilities.

## License

This project is licensed under the MIT License.

---

For more information, please refer to the individual scripts and ensure you have the necessary API access keys configured as per OpenAI's usage policies.
