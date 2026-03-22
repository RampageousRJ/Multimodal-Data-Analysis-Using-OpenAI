# Multimodal Data Analysis Using OpenAI
[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-blue.svg)](https://openai.com/api/)

## Overview
The "Multimodal Data Analysis Using OpenAI" project provides a comprehensive framework for analyzing and processing text, audio, and image data via OpenAI's advanced models. It serves as a versatile toolset for executing complex data processing tasks including text analysis, audio transcription, and image interpretation with streamlined database interaction. This project enables users to leverage the power of OpenAI models for advanced data analysis, making it an ideal solution for a wide range of applications, from research and development to business intelligence and beyond.

## Key Features
*   **Multimodal Data Handling**: Comprehensive support for text, audio, and image data modalities.
*   **OpenAI Integration**: Harnesses the power of OpenAI models for advanced data analysis.
*   **Database Management**: Efficient data management and retrieval powered by robust database utilities.
*   **Text Analysis**: Utilize `openai_text.py` for sentiment analysis of text or CSV files.
*   **Audio Processing**: Leverage `openai_audio.py` to transcribe, translate, or analyze sentiment of audio files.
*   **Image Analysis**: Use `openai_image.py` for captioning or answering questions about images.
*   **Database Utilities**: Query a SQLite database using natural language with `openai_database.py`.

## Architecture / How It Works
The project architecture is based on a microservices approach, where each modality (text, audio, image) is handled by a separate module. The `main.py` script serves as the entry point, orchestrating the different modules and providing a unified interface for the user.
```markdown
+---------------+
|  main.py     |
+---------------+
         |
         |
         v
+---------------+
|  openai_text  |
|  openai_audio|
|  openai_image|
+---------------+
         |
         |
         v
+---------------+
|  openai_database|
+---------------+
```

## Project Structure
```markdown
./
├── .env
├── .python-version
├── README.md
├── db_utils.py
├── main.py
├── openai_audio.py
├── openai_database.py
├── openai_image.py
├── openai_text.py
├── pyproject.toml
├── sync_hooks.sh
├── data/
│   ├── README.md
│   ├── data.db
│   ├── harvard.wav
├── agents/
│   ├── README.md
│   ├── agents/readme_agents/
│   │   ├── README.md
│   │   ├── generate_readme.py
│   │   ├── pre_commit_readme.py
```

## Prerequisites
*   Python 3.14+
*   OpenAI API key
*   `pip` package manager
*   `uv` package (for MCP server)

## Installation & Setup
```bash
# Clone the repository
git clone https://github.com/RampageousRJ/Multimodal-Data-Analysis-Using-OpenAI.git

# Navigate to the project directory
cd Multimodal-Data-Analysis-Using-OpenAI

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt

# Run the sync_hooks.sh script to set up the MCP server
./sync_hooks.sh
```

## Configuration
| Environment Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API key |
| `MCP_SERVER_PORT` | MCP server port |
| `MCP_SERVER_HOST` | MCP server host |

## Usage
### Text Analysis
```bash
# Analyze single text
python openai_text.py -text "This is a great product!"

# Analyze CSV file (must have 'text' column)
python openai_text.py -path data/reviews.csv
```

### Audio Processing
```bash
# Transcribe audio
python openai_audio.py -path data/audio.wav

# Translate audio to target language
python openai_audio.py -path data/audio.wav -translate Spanish

# Analyze sentiment of audio content
python openai_audio.py -path data/audio.wav -sentiment
```

### Image Analysis
```bash
# Caption a local image
python openai_image.py -image_path data/image.jpg

# Answer a question about a local image
python openai_image.py -image_path data/image.jpg -question "What color is the car?"

# Analyze an image from URL
python openai_image.py -image_url https://example.com/image.jpg
```

### Database Utilities
```bash
python openai_database.py -path data/data.db -question "Show me all users from New York"
```

## Contributing
Contributions are welcome! Please submit a pull request with your changes and a brief description of what you've added or fixed.

## License
This project is licensed under the MIT License.