import os
import re
import pandas as pd
import nltk
from itertools import combinations
from flair.data import Sentence
from flair.models import SequenceTagger
import spacy

# Ensure NLTK resources are downloaded
nltk.download('punkt')
nltk.download('wordnet')

# Load the flair model
model_name = "flair/ner-german-large"
tagger = SequenceTagger.load(model_name)

# Load the spaCy model
nlp = spacy.load("de_core_news_sm")

# Define the directory containing the text files
directory = ("C:/Users/Ahmad-PC/Desktop/Both")  # Replace with the path to your text files

# Read the content of each text file into a dictionary
texts = {}
for filename in os.listdir(directory):
    if filename.endswith(".txt"):
        text_id = os.path.splitext(filename)[0]
        with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
            texts[text_id] = file.read()

# Define regular expressions for date, time, year, and month
date_pattern = r'\b(\d{1,2}\.\s?\w+\s?\d{2,4}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b'
time_pattern = r'\b(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\b'
year_pattern = r'\b(18\d{2}|19\d{2})\b'  # Updated pattern to match 1800s and 1900s
month_pattern = r'\b(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\b'


# Custom preprocessing function based on the provided code
def custom_preprocess_text(text):
    # Normalize text: lowercase but keep periods
    normalized_text = text.lower()

    # Tokenize the text
    words = nltk.word_tokenize(normalized_text)

    # Create a custom stopwords list for Low German
    custom_stopwords = {
        'de', 'dat', 'en', 'to', 'op', 'för', 'di', 'wat', 'mit', 'ik', 'du', 'he',
        'se', 'wi', 'ji', 'se', 'dat', 'is', 'in', 'an', 'as', 'bi', 'doot', 'een'
    }

    # Remove stopwords but keep periods
    filtered_words = [word for word in words if word not in custom_stopwords or word == '.']

    # Lemmatization
    lemmatizer = nltk.WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]

    # Recreate the text from lemmatized words
    preprocessed_text = ' '.join(lemmatized_words)
    return preprocessed_text

# Function to calculate word distances
def calculate_word_distances(text):
    # Tokenize the text
    words = text.split()

    # Assign position numbers
    word_positions = {i: word for i, word in enumerate(words)}

    # Calculate word distances
    word_distances = []
    for (pos1, word1), (pos2, word2) in combinations(word_positions.items(), 2):
        distance = abs(pos1 - pos2)
        word_distances.append((pos1, pos2, distance))

    return word_positions, word_distances

# Function to process each text
def process_text(text, text_id):
    # Custom preprocess the text
    text = custom_preprocess_text(text)

    # Calculate word distances
    word_positions, word_distances = calculate_word_distances(text)

    # Split the text into sentences (assuming each line is a sentence)
    sentences = [Sentence(text)]  # Treat the entire text as one sentence

    # Predict named entities for each sentence
    for sentence in sentences:
        tagger.predict(sentence)

    # Collect results
    all_results = []

    for sentence in sentences:
        doc = nlp(sentence.to_original_text())

        # Find entities using regex
        dates = re.findall(date_pattern, sentence.to_original_text())
        times = re.findall(time_pattern, sentence.to_original_text())
        years = re.findall(year_pattern, sentence.to_original_text())
        months = re.findall(month_pattern, sentence.to_original_text())

        # Combine date, time, year, and month into a single Date entity if present
        combined_date = ' '.join(dates + times + years + months).strip()
        if combined_date:
            for match in re.finditer(re.escape(combined_date), sentence.to_original_text()):
                start_pos = match.start()
                all_results.append({
                    'Brief ID': text_id,
                    'Type': 'DATE',
                    'Entity': combined_date,
                    'Score': 1.0,
                    'Position': start_pos,
                    'Distance': 0  # Distance is zero as this is a single entity
                })

        # Collect the flair NER results with score > 0.90
        for entity in sentence.get_spans('ner'):
            if entity.score > 0.90:
                start_pos = sentence.to_original_text().find(entity.text)
                all_results.append({
                    'Brief ID': text_id,
                    'Type': entity.get_label('ner').value,
                    'Entity': entity.text,
                    'Score': entity.score,
                    'Position': start_pos,
                    'Distance': 0  # Distance is zero as this is a single entity
                })

    # Add word distances as a feature
    for wd in word_distances:
        all_results.append({
            'Brief ID': text_id,
            'Type': 'WORD_DISTANCE',
            'Entity': f'{word_positions[wd[0]]}-{word_positions[wd[1]]}',
            'Score': 1.0,
            'Position': wd[0],
            'Distance': wd[2]
        })

    return all_results

# Process each text separately and collect results
all_texts_results = []
for text_id, text in texts.items():
    all_texts_results.extend(process_text(text, text_id))

# Convert to DataFrame
results_df = pd.DataFrame(all_texts_results)

# Filter out WORD_DISTANCE types if needed
results_df = results_df[results_df['Type'] != 'WORD_DISTANCE']

# Save DataFrame to CSV
output_file_path = "C:/Users/Ahmad-PC/Desktop/NER/Result.csv"
results_df.to_csv(output_file_path, index=False)

print(f"NER results saved to {output_file_path}")
