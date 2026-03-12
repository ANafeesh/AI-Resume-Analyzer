import PyPDF2
import docx

def extract_text(file_path):

    text = ""

    if file_path.endswith(".pdf"):

        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            for page in reader.pages:
                text += page.extract_text()

    elif file_path.endswith(".docx"):

        doc = docx.Document(file_path)

        for para in doc.paragraphs:
            text += para.text

    return text.lower()