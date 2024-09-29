import google.generativeai as genai
import PyPDF2
import re
import os

# Configure the Gemini API
genai.configure(api_key="AIzaSyAcpkdxOkgN0iPb_tgq3ZV_pFVpotx_-gA")

# Generation config for Gemini API
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the generative model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Function to extract text from the PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# Function to generate MCQs using Gemini API
def generate_mcqs(text):
    prompt = f"Generate MCQs with always 4 options (labeled a, b, c, d) and an answer based on the following text:\n\n{text}"
    response = model.generate_content(prompt)
    if not response.text:
        raise ValueError("No MCQs were generated. Check the input text.")
    return response.text.strip()

# Function to clean text (removing special characters)
def clean_text(text):
    cleaned_text = re.sub(r"[*]", "", text)
    cleaned_text = re.sub(r"[^\w\s,.?]", "", cleaned_text)
    return cleaned_text

# Delete files if they exist
def delete_files_if_exist(*file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

# Save questions to a file
def save_questions_to_file(mcqs, question_file):
    current_question = ""
    with open(question_file, 'w', encoding='utf-8') as f:
        for line in mcqs.splitlines():
            line = line.strip()
            if re.match(r'^\d+\.', line):  # Check for question number
                if current_question:
                    f.write(current_question + '\n')
                current_question = line
        if current_question:
            f.write(current_question + '\n')

# Save options to a file
def save_options_to_file(mcqs, options_file):
    with open(options_file, 'w', encoding='utf-8') as f:
        for line in mcqs.splitlines():
            if re.match(r'^[a-d]\s', line):  # Match for options (a, b, c, d)
                f.write(line + '\n')

# Save answers to a file
def save_answers_to_file(mcqs, answers_file):
    with open(answers_file, 'w', encoding='utf-8') as f:
        for line in mcqs.splitlines():
            if re.match(r'^Answer', line):  # Match for the answer line
                f.write(line + '\n')

# Function to ask questions from the user and calculate the score
def ask_questions(question_file, options_file, answers_file):
    score = 0
    with open(question_file, 'r', encoding='utf-8') as qf, \
         open(options_file, 'r', encoding='utf-8') as of, \
         open(answers_file, 'r', encoding='utf-8') as af:
        
        questions = qf.readlines()
        options = of.readlines()
        answers = af.readlines()

        question_idx = 0
        for question in questions:
            print(question.strip())

            # Display 4 options for the current question
            for i in range(4):
                print(options[question_idx * 4 + i].strip())
            
            answer = input("Your answer (a/b/c/d): ").strip().lower()

            # Extract the correct answer option
            correct_answer = answers[question_idx].split()[1].strip().lower()

            if answer == correct_answer:
                score += 1

            question_idx += 1

    print(f"Your score: {score}/{len(questions)}")
    return score

# Function to save the score to a file
def save_score_to_file(score, score_file):
    with open(score_file, 'w', encoding='utf-8') as f:
        f.write(f"Score: {score}\n")

# Save raw MCQs to a file
def save_mcqs_to_file(mcqs, mcqs_path):
    with open(mcqs_path, 'w', encoding='utf-8') as f:
        f.write(mcqs)

# Save cleaned MCQs to a file
def save_cleaned_text_to_file(cleaned_text, cleaned_txt_path):
    with open(cleaned_txt_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)

# Example paths (adjust these paths as necessary)
pdf_path = r"D:\Projects ALL\Practice Apps models\preception\Backend\input_pdfs\geah103.pdf"
mcqs_path = './mcqs.txt'
cleaned_txt_path = './cleaned_mcqs.txt'
question_file = './questions.txt'
options_file = './options.txt'
answers_file = './answers.txt'
score_file = './score.txt'

try:
    # Delete previous files if they exist
    delete_files_if_exist(mcqs_path, cleaned_txt_path, question_file, options_file, answers_file, score_file)

    # Extract text from the PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        raise ValueError("No text extracted from PDF. Check the PDF file.")

    # Generate MCQs
    mcqs = generate_mcqs(extracted_text)

    # Save raw MCQs to a file
    save_mcqs_to_file(mcqs, mcqs_path)

    # Clean the MCQs
    cleaned_mcqs = clean_text(mcqs)

    # Save cleaned MCQs to a file
    save_cleaned_text_to_file(cleaned_mcqs, cleaned_txt_path)

    # Save questions, options, and answers to separate files
    save_questions_to_file(cleaned_mcqs, question_file)
    save_options_to_file(cleaned_mcqs, options_file)
    save_answers_to_file(cleaned_mcqs, answers_file)

    # Ask questions to the user and calculate the score
    score = ask_questions(question_file, options_file, answers_file)

    # Save the score to a file
    save_score_to_file(score, score_file)

    print("MCQs generated, cleaned, and saved to the files successfully.")

except Exception as e:
    print(f"An error occurred: {str(e)}")
