import logging
import re
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Global variable to cache the reader to avoid reloading models on every call
_reader = None

def get_reader():
    """Lazy load the easyocr reader"""
    global _reader
    if _reader is None:
        try:
            import easyocr
            # Initialize with English. You can add more languages like 'kh' if easyocr supports it adequately.
            _reader = easyocr.Reader(['en'])
        except ImportError:
            logger.error("easyocr not installed. Please install it with 'pip install easyocr'")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize easyocr: {e}")
            return None
    return _reader

def extract_receipt_data(image_path: str) -> dict:
    """
    Extract high-precision data from a receipt image.
    Returns: {
        'amount': float,
        'trx_id': str,
        'date': datetime object or None
    }
    """
    reader = get_reader()
    if not reader:
        return {'amount': None, 'trx_id': '', 'date': None}

    data = {
        'amount': None,
        'trx_id': '',
        'date': None
    }

    try:
        # readtext returns a list of tuples: (bbox, text, confidence)
        results = reader.readtext(image_path)
        
        # Join all text for easier regex searching
        full_text = " ".join([res[1] for res in results])
        logger.info(f"OCR Full Text: {full_text}")

        # 1. Extract Amount
        # Matches: "2.00", "$2.00", "- $2.00", "Amount: - $2.00"
        amount_patterns = [
            r"(?:Amount|Total|Sum)[:\s]*[-+]?\s*\$?\s*(\d+\.\d+)",
            r"[-+]?\s*\$(\d+\.\d+)", # Large symbol at top: $2.00
            r"(\d+\.\d+)\s*USD"
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['amount'] = float(match.group(1))
                break

        # 2. Extract Transaction ID
        # Matches: "Transaction ID: 000245426017AJUB", "Trx. ID: 47636544918"
        # We prioritize "Transaction ID" over other forms to avoid Merchant ID
        trx_patterns = [
            r"Transaction\s*ID[:\s]*([A-Z0-9]{8,})",
            r"Trx\.?\s*ID[:\s]*([A-Z0-9]{8,})",
            r"Reference\s*#?[:\s]*([A-Z0-9]{8,})",
            r"Ref[:\s]*([A-Z0-9]{8,})",
            r"ID[:\s]*([0-9]{10,})"
        ]
        for pattern in trx_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['trx_id'] = match.group(1).strip()
                break

        # 3. Extract Transaction Date
        # Format 1 (ABA): "Jan 17, 2026 07:20 AM" -> %b %d, %Y %I:%M %p
        # Format 2 (Wing): "17-01-2026 | 07:17:01 AM" -> %d-%m-%Y | %I:%M:%S %p
        data_match = None
        
        # Try Wing Format first (Specific)
        wing_date_pattern = r"(\d{2}-\d{2}-\d{4}\s*\|\s*\d{1,2}:\d{2}:\d{2}\s*[AP]M)"
        match = re.search(wing_date_pattern, full_text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            try:
                data['date'] = datetime.strptime(date_str, "%d-%m-%Y | %I:%M:%S %p")
            except: pass

        # Try ABA/Standard Format if Wing failed
        if not data['date']:
            aba_date_pattern = r"([A-Z]{3}\s\d{1,2},\s\d{4}\s\d{1,2}:\d{2}\s*[AP]M)"
            match = re.search(aba_date_pattern, full_text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                try:
                    data['date'] = datetime.strptime(date_str, "%b %d, %Y %I:%M %p")
                except: pass

    except Exception as e:
        logger.error(f"Error during OCR extraction: {e}")
    
    return data
