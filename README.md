Invoice Parser
Show Image
Overview
Invoice Parser is a powerful terminal-based tool that extracts structured data from invoice images and PDFs using the vision capabilities of the Granite 3.2 vision model via Ollama. This tool streamlines the process of digitizing and standardizing invoice information for accounting, bookkeeping, and data entry tasks.
Features

📄 Supports both PDF and image formats (PNG, JPG, JPEG)
🔍 Intelligent data extraction using Granite 3.2 vision model
🧠 Extracts comprehensive invoice details including:

Basic invoice information (number, dates)
Vendor and customer details
Line items with quantities and prices
Financial totals and payment terms


📊 Displays extracted data with syntax highlighting
💾 Exports data to JSON files
🗂️ Interactive file browser for selecting invoices
📝 Detailed logging for troubleshooting

Requirements

Python 3.8+
Ollama server running with the Granite 3.2 vision model
Poppler (for PDF processing)

Installation
1. Clone the repository
bashCopygit clone https://github.com/yourusername/invoice-parser.git
cd invoice-parser
2. Install dependencies
bashCopypip install -r requirements.txt
3. Install Poppler (required for PDF processing)
On macOS:
bashCopybrew install poppler
On Ubuntu/Debian:
bashCopysudo apt-get install poppler-utils
On Windows:
Download and install from poppler for Windows
4. Configure Ollama
Ensure Ollama is running and the Granite 3.2 vision model is available:
bashCopyollama pull granite:3.2
Configuration
Edit the following settings in the script if needed:
pythonCopyOLLAMA_URL = "https://ollama.congzhoumachinery.com"  # Change to your Ollama server URL
OLLAMA_MODEL = "granite:3.2"  # Ensure this matches your model name in Ollama
Usage
Run the tool with:
bashCopypython invoice_parser.py
Then follow the interactive prompts to:

Navigate to and select an invoice file (PDF or image)
Wait while the invoice is processed
Review the extracted data
Optionally save the data to a JSON file

Example Output
jsonCopy{
  "invoice_number": "INV-12345",
  "invoice_date": "2023-05-15",
  "due_date": "2023-06-15",
  "vendor": {
    "name": "ABC Supplies Ltd.",
    "address": "123 Business St., Suite 456, New York, NY 10001",
    "phone": "(555) 123-4567",
    "email": "billing@abcsupplies.com",
    "tax_id": "12-3456789"
  },
  "customer": {
    "name": "XYZ Corporation",
    "address": "789 Corporate Ave., Chicago, IL 60601",
    "phone": "(555) 987-6543",
    "email": "accounts@xyzcorp.com"
  },
  "items": [
    {
      "description": "Premium Widget A",
      "quantity": 5,
      "unit_price": 29.99,
      "total_price": 149.95
    },
    {
      "description": "Deluxe Gadget B",
      "quantity": 2,
      "unit_price": 49.99,
      "total_price": 99.98
    }
  ],
  "subtotal": 249.93,
  "tax": 20.00,
  "discount": 10.00,
  "shipping": 15.00,
  "total_amount": 274.93,
  "payment_terms": "Net 30",
  "payment_method": "Bank Transfer",
  "notes": "Please include invoice number in payment reference."
}
Troubleshooting

Check the generated invoice_parser.log file for detailed error messages
Ensure your Ollama server is running and accessible
Verify that the Granite 3.2 vision model is properly installed in Ollama
For PDF processing issues, confirm that Poppler is correctly installed

License
MIT License
Acknowledgements

Ollama for the local model hosting
Granite AI for the vision model capabilities
