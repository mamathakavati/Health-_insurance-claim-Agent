
import fitz


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from an uploaded PDF file.
    """

    pdf_bytes = uploaded_file.getvalue()

    extracted_text = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        for page_number, page in enumerate(pdf, start=1):
            page_text = page.get_text()

            if page_text.strip():
                extracted_text.append(
                    f"\n--- Page {page_number} ---\n{page_text}"
                )

    return "\n".join(extracted_text)
