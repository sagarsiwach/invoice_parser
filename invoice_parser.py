#!/usr/bin/env python3
"""
Invoice Parser - A terminal-based tool to extract structured data from invoice images/PDFs
using the vision capabilities of Granite 3.2 vision model via Ollama.
"""
import os
import sys
import json
import base64
import tempfile
from pathlib import Path
from datetime import datetime
import requests
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from pyfiglet import Figlet
from colorama import init, Fore, Style
from loguru import logger
from PIL import Image
from pdf2image import convert_from_path

# Configuration
OLLAMA_URL = "https://ollama.congzhoumachinery.com"
OLLAMA_MODEL = "granite3.2-vision:latest"  # Matches your model registry
APP_NAME = "Invoice Parser"
APP_VERSION = "1.0.0"
APP_COLOR = "blue"

# JSON Schema for invoice data
INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"},
        "invoice_date": {"type": "string", "format": "date"},
        "due_date": {"type": "string", "format": "date"},
        "vendor": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"},
                "tax_id": {"type": "string"}
            },
            "required": ["name"]
        },
        "customer": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name"]
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"},
                    "total_price": {"type": "number"}
                },
                "required": ["description", "quantity", "unit_price"]
            }
        },
        "subtotal": {"type": "number"},
        "tax": {"type": "number"},
        "discount": {"type": "number"},  # Fixed the syntax error here
        "shipping": {"type": "number"},
        "total_amount": {"type": "number"},
        "payment_terms": {"type": "string"},
        "payment_method": {"type": "string"},
        "notes": {"type": "string"}
    },
    "required": ["invoice_number", "invoice_date", "total_amount"]
}

# Initialize components
init()
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan> - <level>{message}</level>", level="DEBUG")
logger.add("invoice_parser.log", rotation="10 MB", level="INFO")
console = Console()

def display_banner():
    """Display the application banner."""
    f = Figlet(font='slant')
    banner = f.renderText(APP_NAME)
    console.print(f"[{APP_COLOR}]{banner}[/{APP_COLOR}]")
    console.print(f"[{APP_COLOR}]Version: {APP_VERSION}[/{APP_COLOR}]")
    console.print(f"[{APP_COLOR}]{'=' * 60}[/{APP_COLOR}]")

def navigate_directories():
    """Navigate directories to select a file."""
    current_dir = os.getcwd()
    file_path = None
    while file_path is None:
        try:
            dir_items = sorted([d for d in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, d))])
            file_items = sorted([f for f in os.listdir(current_dir)
                         if os.path.isfile(os.path.join(current_dir, f)) and
                         f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))])
            choices = [("📁 .. (Go up one directory)", "..")] + \
                      [(f"📁 {d}/", d) for d in dir_items] + \
                      [(f"📄 {f}", f) for f in file_items]

            questions = [
                inquirer.List('choice',
                              message=f"Current directory: {current_dir}",
                              choices=choices,
                              carousel=True),
            ]
            answers = inquirer.prompt(questions)
            if not answers:
                console.print("[red]Selection cancelled. Exiting...[/red]")
                sys.exit(1)

            choice = answers['choice']
            if choice == "..":
                current_dir = os.path.dirname(current_dir)
            elif choice in dir_items:
                current_dir = os.path.join(current_dir, choice)
            else:
                file_path = os.path.join(current_dir, choice)
        except Exception as e:
            logger.error(f"Directory navigation error: {e}")
            console.print(f"[red]Directory navigation error: {e}[/red]")
            current_dir = os.path.expanduser("~")  # Reset to home directory on error

    return file_path

def get_file_as_base64(file_path):
    """Convert file to base64 for API transmission."""
    try:
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error converting file to base64: {e}")
        console.print(f"[red]Error converting file to base64: {e}[/red]")
        return None

def extract_invoice_data(file_path):
    """Extract invoice data using Granite's vision capabilities."""
    file_ext = Path(file_path).suffix.lower()
    temp_dir = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Processing document...", total=None)

        # Handle PDF conversion
        if file_ext == '.pdf':
            progress.update(task, description="[cyan]Converting PDF to images...")
            temp_dir = tempfile.mkdtemp()
            try:
                logger.info(f"Converting PDF: {file_path}")
                logger.info(f"Temp directory: {temp_dir}")

                # Make sure we have proper poppler installation for PDF conversion
                images = convert_from_path(pdf_path=file_path, output_folder=temp_dir)

                if not images or len(images) == 0:
                    raise ValueError("PDF conversion produced no images")

                image_path = os.path.join(temp_dir, "page_0.png")
                logger.info(f"Saving first page to: {image_path}")
                images[0].save(image_path, "PNG")

                # Verify file was created
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Failed to save image at {image_path}")

                file_to_process = image_path
                logger.info(f"Successfully prepared PDF image at: {file_to_process}")
            except Exception as e:
                logger.error(f"PDF conversion error: {e}")
                console.print(f"[red]PDF conversion error: {e}[/red]")
                progress.remove_task(task)

                # Clean up temp directory
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        import shutil
                        shutil.rmtree(temp_dir)
                    except Exception as cleanup_err:
                        logger.warning(f"Failed to clean up temp directory: {cleanup_err}")

                return None
        else:
            file_to_process = file_path
            logger.info(f"Processing image file: {file_to_process}")

        # Prepare image for processing
        progress.update(task, description="[cyan]Preparing image for analysis...")
        image_base64 = get_file_as_base64(file_to_process)

        # Clean up temp directory if PDF was processed
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temporary directory")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")

        if not image_base64:
            progress.remove_task(task)
            return None

        # Create API request with proper image handling
        schema_str = json.dumps(INVOICE_SCHEMA, indent=2)
        progress.update(task, description="[cyan]Analyzing invoice with Granite Vision...")

        # Prepare API request based on Ollama's multimodal API format
        try:
            # This is the correct format for the Ollama API with images
            api_request = {
                "model": OLLAMA_MODEL,
                "prompt": f"Analyze this invoice image and extract data according to this schema:\n{schema_str}\n\nReturn ONLY valid JSON without explanations.",
                "images": [image_base64],  # Correct way to send images to Ollama
                "stream": False
            }

            logger.debug(f"Sending request to: {OLLAMA_URL}/api/generate")
            logger.debug(f"Using model: {OLLAMA_MODEL}")

            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json=api_request,
                timeout=120
            )

            progress.remove_task(task)

            if response.status_code != 200:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                console.print(f"[red]API Error: {response.status_code} - {response.text}[/red]")
                return None

            # Process response
            response_json = response.json()
            logger.debug(f"Response received with keys: {list(response_json.keys())}")

            llm_response = response_json.get('response', '')
            logger.debug(f"Response preview: {llm_response[:100]}...")

            try:
                # First try direct JSON parsing in case model returned clean JSON
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from the text
                    json_start = llm_response.find('{')
                    json_end = llm_response.rfind('}') + 1

                    if json_start >= 0 and json_end > json_start:
                        json_str = llm_response[json_start:json_end]
                        parsed_data = json.loads(json_str)
                        logger.info("Successfully extracted JSON from response")
                        return parsed_data
                    else:
                        logger.error("No JSON found in response")
                        logger.debug(f"Response content: {llm_response}")
                        console.print("[red]No valid JSON found in the model response[/red]")
                        return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                console.print(f"[red]JSON parse error: {e}[/red]")
                return None

        except requests.exceptions.RequestException as e:
            progress.remove_task(task)
            logger.error(f"API request failed: {e}")
            console.print(f"[red]API request failed: {e}[/red]")
            return None
        except Exception as e:
            progress.remove_task(task)
            logger.error(f"Unexpected error during API request: {e}")
            console.print(f"[red]Unexpected error: {e}[/red]")
            return None

def display_invoice_data(invoice_data):
    """Display the extracted invoice data in a user-friendly format."""
    if not invoice_data:
        console.print("[yellow]No invoice data was extracted[/yellow]")
        return

    try:
        # Format and display the JSON with syntax highlighting
        json_str = json.dumps(invoice_data, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="[bold green]Extracted Invoice Data[/bold green]", expand=False))

        # Save option
        questions = [
            inquirer.Confirm('save', message='Save to JSON file?', default=True),
        ]
        answers = inquirer.prompt(questions)
        if answers and answers['save']:
            default_filename = f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            file_questions = [
                inquirer.Text('filename', message="Enter filename", default=default_filename),
            ]
            file_answers = inquirer.prompt(file_questions)

            if file_answers:
                filename = file_answers['filename']
                with open(filename, 'w') as f:
                    json.dump(invoice_data, f, indent=2)
                console.print(f"[green]Invoice data saved to {filename}[/green]")
    except Exception as e:
        logger.error(f"Display error: {e}")
        console.print(f"[red]Error displaying invoice data: {e}[/red]")

def main():
    """Main application entry point."""
    try:
        display_banner()
        console.print("[yellow]Extracting structured data from invoices using Granite Vision[/yellow]")
        console.print()

        # Check API connectivity
        try:
            version_response = requests.get(f"{OLLAMA_URL}/api/version", timeout=5)
            version_info = version_response.json()
            console.print(f"[green]✓ Connected to Ollama API at {OLLAMA_URL}[/green]")
            console.print(f"[green]✓ Ollama version: {version_info.get('version', 'unknown')}[/green]")

            # Check if the model is available
            models_response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            models = models_response.json().get('models', [])
            model_names = [m.get('name') for m in models]

            if OLLAMA_MODEL in model_names:
                console.print(f"[green]✓ Model {OLLAMA_MODEL} is available[/green]")
            else:
                console.print(f"[yellow]⚠ Model {OLLAMA_MODEL} not found in available models. Available models: {', '.join(model_names)}[/yellow]")

        except requests.exceptions.RequestException as e:
            logger.error(f"API connection failed: {e}")
            console.print(f"[red]✗ Could not connect to Ollama API: {e}[/red]")
            console.print(f"[yellow]Please ensure Ollama is running and accessible at {OLLAMA_URL}[/yellow]")
            sys.exit(1)

        console.print()
        console.print("[bold]Navigate and select an invoice file (PDF or image)[/bold]")

        file_path = navigate_directories()
        console.print(f"[green]Selected file: {file_path}[/green]")

        invoice_data = extract_invoice_data(file_path)
        display_invoice_data(invoice_data)

        console.print()
        console.print("[green]Thank you for using Invoice Parser![/green]")
    except Exception as e:
        logger.error(f"Application error: {e}")
        console.print(f"[red]Application error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)
