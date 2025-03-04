import os
import streamlit as st
from google.cloud import vision
from PIL import Image
from io import BytesIO
import fitz  # PyMuPDF
import pandas as pd

# Access Google Cloud Vision API key from Streamlit secrets (set in Streamlit Cloud)
google_vision_api_key = st.secrets["GOOGLE_API_KEY"]

# Initialize Google Cloud Vision client with the API key (using the correct URL format)
client = vision.ImageAnnotatorClient()

# Function to perform OCR using Google Cloud Vision
def extract_text_from_image_with_vision(image_data):
    image = vision.Image(content=image_data)

    # Set API key to the client as the 'credentials' argument
    client._transport._credentials = None
    client._transport._host = f'https://vision.googleapis.com/v1/images:annotate?key={google_vision_api_key}'

    response = client.text_detection(image=image)
    
    # Extract text from the response
    if response.error.message:
        raise Exception(f"Google Cloud Vision API Error: {response.error.message}")
    else:
        texts = response.text_annotations
        return texts[0].description if texts else ""  # Return the full detected text

# Function to extract text from PDF using images and Google Cloud Vision OCR
def extract_graphics_as_images_for_ocr(uploaded_file):
    # Read the uploaded file as a byte stream
    pdf_bytes = uploaded_file.read()
    
    # Open the PDF with PyMuPDF from the byte stream
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    ocr_texts = []

    for page in doc:
        images = page.get_images(full=True)  # Extract images from the page
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            
            # Apply OCR using Google Cloud Vision on the extracted image
            ocr_result = extract_text_from_image_with_vision(image_data)
            if ocr_result.strip():
                ocr_texts.append(f"Page {page.number + 1}, Image {img_index}: {ocr_result}")

    return ocr_texts

# Function to extract PDF metadata
def detect_pdf_metadata(uploaded_file):
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    metadata = doc.metadata
    return metadata

# Main function to extract data from PDF
def extract_data_from_pdf(uploaded_file):
    ocr_text = extract_graphics_as_images_for_ocr(uploaded_file)  # Extract OCR text from images using Google Cloud Vision
    metadata = detect_pdf_metadata(uploaded_file)  # Extract metadata for extra details
    
    # Combine all extracted data
    return {
        "OCR Text": ocr_text,
        "Metadata": metadata
    }

# Streamlit user interface
st.title("PDF Data Extractor with Google Cloud Vision OCR")
st.sidebar.header("Upload Your PDF")

# Upload PDF
uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.write("Processing the file...")

    # Extract the necessary data from the uploaded PDF
    try:
        extracted_data = extract_data_from_pdf(uploaded_file)

        # Display extracted data
        st.subheader("OCR Extracted Text from Images using Google Cloud Vision")
        st.write(extracted_data["OCR Text"])

        st.subheader("PDF Metadata")
        st.write(extracted_data["Metadata"])
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
