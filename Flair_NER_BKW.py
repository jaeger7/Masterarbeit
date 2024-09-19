import os
import re
import pandas as pd
from itertools import combinations
from flair.data import Sentence
from flair.models import SequenceTagger
import spacy

# Load the flair model (only once)
model_name = "flair/ner-german-large"
tagger = SequenceTagger.load(model_name)

# Load the spaCy model (only once)
nlp = spacy.load("de_core_news_sm")

# Define the root directory containing the BKW/Brief/Blätter/txt_files
root_directory = ("C:/Users/Ahmad-PC/Desktop/BKW")

# Define regex for Roman numeral months, abbreviated months, and full months
roman_numeral_months = r'(I{1,3}|IV|V|VI|VII|VIII|IX|X|XI|XII)'

# Abbreviated month names and full month names
months_pattern = r'(Januar|Jan|Februar|Feb|März|Mär|April|Apr|Mai|Juni|Jun|Juli|Jul|August|Aug|September|Sep|Oktober|Okt|November|Nova|Dezember|Dez)'

# General date pattern handling day, Roman numerals, months, and two/four-digit years
date_pattern = rf'\b(\d{{1,2}}\.\s?({roman_numeral_months}|{months_pattern}|[0-9]{{1,2}})\s?\.\s?\d{{2,4}})\b'

# Debugging function: Check if regex captures dates properly
def extract_dates(text):
    dates = re.findall(date_pattern, text)
    if dates:
        print(f"Extracted dates: {dates}")
    else:
        print("No dates found.")
    return dates

# Function to calculate word distances
def calculate_word_distances(text):
    words = text.split()
    word_positions = {i: word for i, word in enumerate(words)}
    word_distances = []
    for (pos1, word1), (pos2, word2) in combinations(word_positions.items(), 2):
        distance = abs(pos1 - pos2)
        word_distances.append((pos1, pos2, distance))
    return word_positions, word_distances

# Function to process each text
def process_text(text, brief_id, blätter_id):
    # Extract dates for debugging
    dates = extract_dates(text)

    # Calculate word distances
    word_positions, word_distances = calculate_word_distances(text)

    sentences = [Sentence(text)]
    for sentence in sentences:
        tagger.predict(sentence)

    all_results = []

    for sentence in sentences:
        doc = nlp(sentence.to_original_text())

        # Add the found dates into the results
        combined_date = ' '.join([d[0] for d in dates]).strip()
        if combined_date:
            for match in re.finditer(re.escape(combined_date), sentence.to_original_text()):
                start_pos = match.start()
                all_results.append({
                    'Brief ID': brief_id,
                    'Blätter ID': blätter_id,
                    'Type': 'DATE',
                    'Entity': combined_date,
                    'Score': 1.0,
                    'Position': start_pos,
                    'Distance': 0
                })

        # Collect the flair NER results with score > 0.90
        for entity in sentence.get_spans('ner'):
            if entity.score > 0.955:
                start_pos = sentence.to_original_text().find(entity.text)
                all_results.append({
                    'Brief ID': brief_id,
                    'Blätter ID': blätter_id,
                    'Type': entity.get_label('ner').value,
                    'Entity': entity.text,
                    'Score': entity.score,
                    'Position': start_pos,
                    'Distance': 0
                })

    for wd in word_distances:
        all_results.append({
            'Brief ID': brief_id,
            'Blätter ID': blätter_id,
            'Type': 'WORD_DISTANCE',
            'Entity': f'{word_positions[wd[0]]}-{word_positions[wd[1]]}',
            'Score': 1.0,
            'Position': wd[0],
            'Distance': wd[2]
        })

    return all_results

# Traverse through the Brief and Blätter folders
all_texts_results = []
for brief_folder in os.listdir(root_directory):
    brief_path = os.path.join(root_directory, brief_folder)
    if os.path.isdir(brief_path):  # Check if it is a folder (Brief)
        brief_id = brief_folder

        for blätter_folder in os.listdir(brief_path):
            blätter_path = os.path.join(brief_path, blätter_folder)
            if os.path.isdir(blätter_path):  # Check if it is a folder (Blätter)
                blätter_id = blätter_folder

                # Process all text files in the Blätter folder
                for filename in os.listdir(blätter_path):
                    if filename.endswith(".txt"):
                        file_path = os.path.join(blätter_path, filename)
                        with open(file_path, 'r', encoding='utf-8') as file:
                            text = file.read()
                            all_texts_results.extend(process_text(text, brief_id, blätter_id))

# Convert results to DataFrame
results_df = pd.DataFrame(all_texts_results)

# Filter out WORD_DISTANCE types if needed
results_df = results_df[results_df['Type'] != 'WORD_DISTANCE']

# Save DataFrame to CSV
output_file_path = "C:/Users/Ahmad-PC/Desktop/NER/Result.csv"
results_df.to_csv(output_file_path, index=False)

print(f"NER results saved to {output_file_path}")
