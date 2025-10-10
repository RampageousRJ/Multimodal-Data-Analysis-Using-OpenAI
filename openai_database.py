import argparse
import os
import re
import openai
from dotenv import load_dotenv
from db_utils import run_query
import sqlite3
load_dotenv()

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

def extract_table_structure(db_path):
    try:
        structure = ""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")

        for row in cursor.fetchall():
            structure += f"{row[0]}\n\n"

        conn.close()
        return structure

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return ''

def create_prompt(structure, question):
    prompt = f"""
    I wish for you to be an expert database administrator and give me a query output for every {question} in natural language.
    Only give me the output, do not explain anything.
    Also enclose your SQL query in triple backticks.
    Keep the query in one line itself.
    Use the following table structure:
    {structure}

    So please give me the SQL query for {question}.
    """
    return prompt

def call_llm(prompt):
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=500,
        temperature=0
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage a simple database of entries.")
    parser.add_argument("-path", type=str, help="Path to the database file.", required=True)
    parser.add_argument("-question", type=str, help="Question in Natural Language", required=True)
    args = parser.parse_args()

    structure = extract_table_structure(args.path)
    print("=== Database Schema ===\n", structure)
    prompt = create_prompt(structure, args.question)
    response = re.sub(r'`', '', call_llm(prompt)).strip()
    print(f'\n\n\n=== Query ===\n {response}')
    results = run_query(args.path, response)
    print(f'\n\n\n=== Results ===\n {results}')
