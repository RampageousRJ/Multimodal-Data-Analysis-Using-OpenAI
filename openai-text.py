import argparse
import dotenv
import openai
import os
import pandas as pd
import csv

dotenv.load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create prompt for sentiment classification
def create_prompt(text):
    instructions = 'You are an expert sentiment classifier. Classify the sentiment of the given text as either "Positive", "Negative" or "Neutral" STRICTLY and nothing else. Not even any other word not even a different case. Do not add any explanations. Just return the sentiment.'
    return f'{instructions}\n\nText: {text}'

# Call the LLM with the given prompt
def call_llm(prompt):
    messages = [
        {'role':'user', 'content':prompt}
    ]
    response = client.chat.completions.create(messages=messages, model="gpt-4o")
    return response.choices[0].message.content

# Classify sentiment for a single text input
def classify_text(text):
    prompt = create_prompt(text)
    return call_llm(prompt)

# Classify sentiments in batches for efficiency
def classify_batch(texts, batch_size=5):
    all_results = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        joined_texts = "\n".join([f"{start+idx+1}. {t}" for idx, t in enumerate(batch)])
        prompt = (
            "You are an expert sentiment classifier. For each numbered text below, "
            "classify it as either 'Positive', 'Negative' or 'Neutral'.\n"
            "Return your output in the exact format:\n"
            "1. Positive\n2. Negative\n3. Positive\n"
            "and nothing else.\n\n"
            f"{joined_texts}"
        )
        response = call_llm(prompt).strip()
        print(f"\n=== Batch {start // batch_size + 1} raw response ===\n{response}\n")
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        batch_results = []
        for line in lines:
            parts = line.split('.', 1)
            if len(parts) == 2:
                sentiment = parts[1].strip()
                batch_results.append(sentiment)
            else:
                print(f"Skipping malformed line: {line}")

        if len(batch_results) != len(batch):
            print(f"Mismatch: expected {len(batch)}, got {len(batch_results)}. Raw:\n{response}")
        all_results.extend(batch_results)
    return all_results

# Validate predicted sentiments against actual sentiments
def validate_sentiment(actual_sentiment, predicted_sentiments):
    correct = sum(1 for actual, predicted in zip(actual_sentiment, predicted_sentiments) if actual.lower() == predicted.lower())
    accuracy = correct / len(actual_sentiment) if actual_sentiment else 0
    return accuracy  
    
# Generate column names using LLM if CSV lacks header
def generate_column_names(random_csv_row):
    columns = random_csv_row.strip().split(',')
    prompt = (
            """
                You are a data expert. Given a CSV row, generate appropriate column names for the data. For example, if the row is:
                1,Positive,This product is great!
                You might suggest column names like:
                id,actual_sentiment,text
                Please note that if there is a column that depicts sentiment, use the name 'actual_sentiment' for that column. 
                Also there must be a column named 'text' if there is any significant amount of text data in the row.
                And STRICTLY adhere to these norms.
            """
        )
    prompt += f"\n\nCSV Row: {random_csv_row}\n\nColumn Names:"
    response = call_llm(prompt).strip()
    column_names = [col.strip() for col in response.split(',')]
    return column_names

# Use Sniffer to check if CSV has header
def csv_has_header(path, sample_bytes=4096):
    sniffer_guess = False
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(sample_bytes)
        sniffer_guess = csv.Sniffer().has_header(sample)
    except Exception:
        sniffer_guess = False
    return sniffer_guess

if __name__ == "__main__":
    # Argument Parsing for CLI
    parser = argparse.ArgumentParser(description="Classify sentiments based on a text or file input.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-text', type=str, help='Text to classify')
    group.add_argument('-path', type=str, help='Path to file containing text to classify')
    args = parser.parse_args()

    # If path is provided, read the CSV and classify sentiments in batch
    if args.path:
        # Check if the CSV has a header, if not then generate column names
        if csv_has_header(args.path):
            df = pd.read_csv(args.path, header=0)
        else:
            first_row_df = pd.read_csv(args.path, header=None, nrows=1)
            first_row = first_row_df.iloc[0].to_csv(index=False, header=False).strip()
            col_names = generate_column_names(first_row)
            df = pd.read_csv(args.path, header=None, names=col_names)

        # Process the CSV file before classification
        df.drop_duplicates(subset=['id'], inplace=True)
        if 'text' not in df.columns:
            raise ValueError("CSV file must contain a 'text' column.")
        
        # Size reduction for testing purposes
        df = df.head(100)

        # Classify sentiments in batch
        predicted_sentiment = classify_batch(df['text'].tolist(), batch_size=50)
        print(predicted_sentiment)

        # If actual sentiment column exists, validate accuracy
        try:
            accuracy = validate_sentiment(df['actual_sentiment'].tolist(), predicted_sentiment)
            print(f"Accuracy: {accuracy * 100:.2f}%")
        except Exception as e:
            print(f"Could not compute accuracy: {e}")

    # If text is provided, classify that single text
    else:
        print(classify_text(args.text))

