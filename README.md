# Certificate OCR System

A complete Tesseract OCR-based document processing application built for the Teerop Pvt. Limited AI \& Machine Learning Internship Task 1.

## Features

* Drag-and-drop certificate upload UI
* JPG, JPEG, PNG, TIFF and multi-page PDF support
* Tesseract OCR text extraction
* OpenCV preprocessing: grayscale, contrast normalization, denoising, adaptive thresholding and deskewing
* Structured extraction of candidate name, certificate title, organization, issue date, certificate number, grade/score and duration
* OCR confidence score
* JSON API responses
* SQLite history storage
* JSON and CSV result export
* Copy-to-clipboard support
* Responsive frontend
* Basic unit/API tests

## Technology Stack

* Python 3.11+
* FastAPI
* Tesseract OCR 5+
* OpenCV
* pytesseract
* pdf2image + Poppler
* SQLite
* HTML/CSS/JavaScript

## Project Structure

```text
certificate-ocr-system/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── extractor.py
│   │   ├── ocr\_engine.py
│   │   └── preprocessor.py
│   ├── models/
│   │   ├── database.py
│   │   └── schemas.py
│   └── utils/
│       ├── file\_handler.py
│       └── validators.py
├── sample\_certificates/
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/index.html
├── tests/
├── uploads/
├── main.py
├── requirements.txt
└── README.md
```

## 1\. Install Python

Use Python 3.11 or newer.

## 2\. Create and activate a virtual environment

### Windows

```bash
python -m venv venv
venv\\Scripts\\activate
python -m pip install --upgrade pip
```

### Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

## 3\. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 4\. Install Tesseract OCR

### Windows

Install Tesseract OCR (the UB Mannheim Windows build is commonly used). During installation, note the location of `tesseract.exe` and add it to the Windows PATH.

If you do not want to modify PATH, set an environment variable before starting the app:

```powershell
$env:TESSERACT\_CMD="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install tesseract-ocr
```

### macOS

```bash
brew install tesseract
```

## 5\. Install Poppler for PDF support

Poppler is required only for PDF conversion.

### Windows

Download a Windows Poppler build, extract it, and add its `Library\\bin` folder to PATH. Alternatively:

```powershell
$env:POPPLER\_PATH="C:\\path\\to\\poppler\\Library\\bin"
```

### Ubuntu/Debian

```bash
sudo apt install poppler-utils
```

### macOS

```bash
brew install poppler
```

## 6\. Run the application

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Interactive FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

|Method|Endpoint|Description|
|-|-|-|
|GET|`/`|Web interface|
|GET|`/health`|Health check|
|POST|`/upload`|Upload and process a certificate|
|POST|`/extract`|Extract certificate data|
|GET|`/results`|Recent stored results|
|GET|`/results/{id}`|Get one extraction result|
|DELETE|`/documents/{id}`|Delete stored document|
|GET|`/results/{id}/json`|Download result as JSON|
|GET|`/results/{id}/csv`|Download extracted fields as CSV|

## Example API Usage

```python
import requests

files = {"file": open("sample\_certificates/sample\_certificate.png", "rb")}
response = requests.post("http://127.0.0.1:8000/extract", files=files)
print(response.json())
```

## Example JSON Response

```json
{
  "id": "d61a16c1363f",
  "filename": "sample\_certificate.png",
  "page\_count": 1,
  "average\_confidence": 93.42,
  "fields": {
    "candidate\_name": "Ali Hassan",
    "certificate\_title": "Machine Learning Fundamentals",
    "organization\_name": "Teerop Pvt. Limited",
    "issue\_date": "12/07/2026",
    "certificate\_number": "TEEROP-2026-001",
    "grade\_score": "A",
    "duration": null,
    "additional\_fields": {"certificate\_type": "Completion"}
  },
  "raw\_text": "...",
  "created\_at": "2026-07-12T10:00:00+00:00"
}
```

## Testing

```bash
python -m pytest tests/
```

## Troubleshooting

### `TesseractNotFoundError`

Install Tesseract and add it to PATH or set `TESSERACT\_CMD`.

### PDF conversion fails

Install Poppler and add it to PATH or set `POPPLER\_PATH`.

### Poor OCR accuracy

Use higher-resolution scans, keep the document straight, avoid shadows, and test alternative Tesseract page segmentation modes if necessary.

### Import errors

Activate the virtual environment and rerun:

```bash
pip install -r requirements.txt
```

## Submission Checklist

* Public GitHub repository
* Complete source code
* README with setup and usage instructions
* `requirements.txt`
* Sample certificates
* UI and result screenshots
* Working OCR extraction
* Clean code and error handling
* Tests passing



\## Application Screenshots



\### Upload Interface

!\[Upload Interface](screenshots/OCR.png)



\### Certificate Preview

!\[Certificate Preview](screenshots/certidicate.png)



\### OCR Extraction Result

!\[OCR Result](screenshots/results.png)

