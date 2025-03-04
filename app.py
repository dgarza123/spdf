import streamlit as st
import fitz  # PyMuPDF
import easyocr
import re
import json
import io
import pandas as pd
from PIL import Image

# ✅ Initialize EasyOCR Reader
reader = easyocr.Reader(["en"])

# ✅ Predefined regex patterns for financial & identity markers
patterns = {
    "Torrens Number": r"\bT\s?\d{6}\b",  
    "Bank Account": r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  
    "Monetary Amount": r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?",  
    "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",  
    "SWIFT Code": r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?\b",  
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",  
    "Tax ID": r"\b\d{2}-\d{7}\b",  
    "Credit Card": r"\b(?:\d{4}[ -]?){3}\d{4}\b",  
    "Phone Number": r"\b(?:\+?1\s?)?(?:\(\d{3}\)|\d{3})[ -.]?\d{3}[ -.]?\d{4}\b",  
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
}

# ✅ Function to extract text from an image using EasyOCR
def extract_text_from_image(image_data):
    try:
        image = Image.open(io.BytesIO(image_data))
        text = reader.readtext(image, detail=0)
        return "\n".join(text) if text else "No text detected."
    except Exception as e:
        return f"❌ OCR Extraction Failed: {e}"

# ✅ Function to extract and analyze images from PDFs
def extract_text_from_pdf_images(uploaded_file):
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    extracted_data = []

    for page in doc:
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]

            # Perform OCR
            ocr_result = extract_text_from_image(image_data)

            if ocr_result.strip():
                extracted_data.append({"Page": page.number + 1, "Text": ocr_result})

    return extracted_data

# ✅ Function to detect financial markers in extracted text
def detect_markers(text):
    found_data = []
    for marker, pattern in patterns.items():
        matches = re.findall(pattern, text)
        for match in matches:
            found_data.append({"Type": marker, "Value": match})
    return found_data

# ✅ Function to process the PDF file
def analyze_pdf(uploaded_file):
    # Extract OCR text
    ocr_data = extract_text_from_pdf_images(uploaded_file)

    # Store extracted entities
    all_entities = []

    for entry in ocr_data:
        detected = detect_markers(entry["Text"])
        if detected:
            all_entities.append({"Page": entry["Page"], "Entities": detected})

    return all_entities

# ✅ Streamlit UI
st.title("📄 Shiva PDF Analyzer - Financial & Identity Data Extraction")
st.sidebar.header("Upload Your PDF")

uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file:
    st.write("⏳ Processing the file...")

    try:
        extracted_entities = analyze_pdf(uploaded_file)

        # ✅ Display Extracted Data
        st.subheader("🔍 Extracted Financial & Identity Data")
        
        if extracted_entities:
            results_df = []
            for page_data in extracted_entities:
                for entity in page_data["Entities"]:
                    results_df.append([page_data["Page"], entity["Type"], entity["Value"]])

            df = pd.DataFrame(results_df, columns=["Page", "Entity Type", "Detected Value"])
            st.write(df)

            # ✅ Save results as JSON file
            json_output = {"document": uploaded_file.name, "entities": extracted_entities}
            json_filename = f"{uploaded_file.name}_results.json"

            with open(json_filename, "w") as json_file:
                json.dump(json_output, json_file, indent=4)

            st.download_button("📥 Download JSON Report", json_filename, json.dumps(json_output), "application/json")
        else:
            st.write("✅ No financial or identity-related markers detected.")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
