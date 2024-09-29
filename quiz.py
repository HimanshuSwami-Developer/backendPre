import google.generativeai as genai
import PyPDF2
import re
import os

# Assuming these functions will save the content to text files
from quiz_game import save_answers_to_file, save_cleaned_text_to_file, save_mcqs_to_file, save_options_to_file, save_questions_to_file

# Configure the Gemini API
genai.configure(api_key="AIzaSyAcpkdxOkgN0iPb_tgq3ZV_pFVpotx_-gA")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def extract_text_from_pdf(pdf_path):
    """Extracts text from the given PDF file."""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def generate_mcqs(text):
    """Generates MCQs using the Gemini model based on the provided text."""
    prompt = f"Generate only MCQs with 4 options and an answer based on the following text:\n\n{text}"
    response = model.generate_content(prompt)
    if not response.text:
        raise ValueError("No MCQs were generated. Check the input text.")
    return response.text.strip()

def clean_text(text):
    """Cleans the text by removing unwanted characters."""
    cleaned_text = re.sub(r"[*]", "", text)
    cleaned_text = re.sub(r"[^\w\s,.?]", "", cleaned_text)
    return cleaned_text

def process_pdf_and_save(filename, input_folder, output_folder):
    """
    Processes the PDF, generates MCQs, cleans them, and saves MCQs, questions, options,
    and answers to respective files.
    """
    pdf_path = os.path.join(input_folder, filename)
    mcqs_path = os.path.join(output_folder, 'mcqs.txt')
    cleaned_txt_path = os.path.join(output_folder, 'cleaned_mcqs.txt')
    options_path = os.path.join(output_folder, 'options.txt')
    answers_path = os.path.join(output_folder, 'answers.txt')

    try:
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(pdf_path)
        if not extracted_text:
            raise ValueError("No text extracted from the PDF. Check the PDF file.")

        # Generate MCQs from the extracted text
        mcqs = generate_mcqs(extracted_text)

        # Save raw MCQs to a file
        save_mcqs_to_file(mcqs, mcqs_path)

        # Clean the generated MCQs text
        cleaned_mcqs = clean_text(mcqs)

        # Save cleaned MCQs to a file
        save_cleaned_text_to_file(cleaned_mcqs, cleaned_txt_path)

        # Save questions, options, and answers to their respective files
        save_questions_to_file(cleaned_mcqs, mcqs_path)
        save_options_to_file(cleaned_mcqs, options_path)
        save_answers_to_file(cleaned_mcqs, answers_path)

        print("MCQs generated, cleaned, and saved successfully.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
input_folder = r"D:\Projects ALL\Practice Apps models\preception\Backend\input_pdfs"
output_folder = r"D:\Projects ALL\Practice Apps models\preception\Backend\output"

filename = "geah103.pdf"

process_pdf_and_save(filename, input_folder, output_folder)
