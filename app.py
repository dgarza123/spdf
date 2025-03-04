import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import fitz  # PyMuPDF

# ✅ Debugging: Print secrets to ensure they're loading correctly
if "gcp_service_account" not in st.secrets:
    st.error("❌ Error: gcp_service_account not found in secrets.toml. Please check the configuration.")
    st.stop()  # Stops execution if secrets are missing

# ✅ Load Google Cloud credentials (Ensures only one instance)
try:
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    client = vision.ImageAnnotatorClient(credentials=credentials)
except Exception as e:
    st.error(f"❌ Failed to initialize Google Cloud Vision client: {e}")
    st.stop()

# ✅ Function to perform OCR using Google Cloud Vision
def extract_text_from_image_with_vision(image_data):
    try:
        image = vision.Image(content=image_data)
        response = client.text_detection(image=image)

        if response.error.message:
            return f"❌ Google Cloud Vision API Error: {response.error.message}"

        texts = response.text_annotations
        return texts[0].description if texts else ""  # Return the full detected text
    except Exception as e:
        return f"❌ OCR Extraction Failed: {e}"

# ✅ Function to extract text from PDF images using Google Cloud Vision OCR
def extract_graphics_as_images_for_ocr(uploaded_file):
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    ocr_texts = []

    for page in doc:
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            
            # Apply OCR using Google Cloud Vision on the extracted image
            ocr_result = extract_text_from_image_with_vision(image_data)
            if ocr_result.strip():
                ocr_texts.append(f"Page {page.number + 1}, Image {img_index}: {ocr_result}")

    return ocr_texts if ocr_texts else ["No text extracted from images."]

# ✅ Function to extract PDF metadata
def detect_pdf_metadata(uploaded_file):
    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        return doc.metadata
    except Exception as e:
        return f"❌ Failed to extract metadata: {e}"

# ✅ Main function to extract data from PDF
def extract_data_from_pdf(uploaded_file):
    return {
        "OCR Text": extract_graphics_as_images_for_ocr(uploaded_file),
        "Metadata": detect_pdf_metadata(uploaded_file)
    }

# ✅ Streamlit user interface
st.title("📄 PDF Data Extractor with Google Cloud Vision OCR")
st.sidebar.header("Upload Your PDF")

# ✅ Upload PDF
uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file:
    st.write("⏳ Processing the file...")

    try:
        extracted_data = extract_data_from_pdf(uploaded_file)

        # ✅ Display extracted OCR text
        st.subheader("📖 OCR Extracted Text from Images")
        st.write("\n".join(extracted_data["OCR Text"]))

        # ✅ Display PDF Metadata
        st.subheader("ℹ️ PDF Metadata")
        st.write(extracted_data["Metadata"])
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
