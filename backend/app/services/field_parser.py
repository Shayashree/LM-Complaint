import re
from typing import Dict, Any, Optional, Tuple, List

class FieldParser:
    """
    Field-specific parser and normalizer under the Legal Metrology (Packaged Commodities) Rules, 2011.
    Features independent, specialized parsers for each statutory field.
    Preserves raw_value while computing normalized_value for legal comparison.
    """

    # Standard metric units recognized under Rule 11 & Schedule III
    WEIGHT_UNITS = {"g", "kg", "mg", "gm", "gms", "gram", "grams", "kilogram", "kilograms"}
    VOLUME_UNITS = {"ml", "l", "ltr", "litre", "litres", "millilitre", "millilitres"}
    COUNT_UNITS = {"n", "unit", "units", "pc", "pcs", "piece", "pieces", "count"}

    def parse_and_normalize(self, field_name: str, raw_text: str) -> Dict[str, Any]:
        """
        Routes text to its specialized parser and returns structured, normalized declaration.
        """
        if not raw_text or str(raw_text).strip() in ["N/A", "null", "None", "", "not detected"]:
            return {
                "raw_value": "NOT_DETECTED",
                "normalized_value": None,
                "is_valid_format": False,
                "status": "NOT_DETECTED"
            }

        text = str(raw_text).strip()

        if field_name == "mrp":
            return self.parse_mrp(text)
        elif field_name == "net_quantity":
            return self.parse_net_quantity(text)
        elif field_name in ["mfg_date", "manufacturing_date", "packing_date"]:
            return self.parse_date(text, is_mfg=True)
        elif field_name in ["best_before", "best_before_or_expiry", "expiry_date"]:
            return self.parse_best_before(text)
        elif field_name == "consumer_care":
            return self.parse_consumer_care(text)
        elif field_name == "unit_sale_price":
            return self.parse_unit_sale_price(text)
        elif field_name in ["manufacturer", "packer", "importer", "manufacturer_name_address"]:
            return self.parse_manufacturer(text)
        elif field_name == "country_of_origin":
            return self.parse_country_of_origin(text)
        elif field_name in ["product_name", "brand"]:
            return self.parse_product_or_brand(text, field_name)
        else:
            return {
                "raw_value": text,
                "normalized_value": {"value": text, "unit": None},
                "is_valid_format": True,
                "status": "VERIFIED"
            }

    def parse_mrp(self, text: str) -> Dict[str, Any]:
        """
        Parses Maximum Retail Price. Checks currency symbols (?, Rs) and mandatory phrase 'incl. of all taxes'.
        """
        cleaned = text.replace(",", "")
        # Look for explicit currency and decimal/integer value
        price_match = re.search(r"(?:\u20b9|Rs\.?|INR)?\s*(\d+(?:\.\d{1,2})?)", cleaned, re.IGNORECASE)
        has_taxes = bool(re.search(r"incl(?:usive)?\.?\s*(?:of)?\s*(?:all)?\s*taxes", cleaned, re.IGNORECASE))

        if price_match:
            val_float = float(price_match.group(1))
            norm = {
                "currency": "INR",
                "amount": val_float,
                "inclusive_of_taxes": has_taxes
            }
            # Rule 6(1)(e): Must include phrase 'inclusive of all taxes'
            return {
                "raw_value": text,
                "normalized_value": norm,
                "is_valid_format": True,
                "has_taxes_declared": has_taxes,
                "status": "VERIFIED" if has_taxes else "REQUIRES_MANUAL_REVIEW",
                "review_reason": None if has_taxes else "MRP lacks statutory phrase 'inclusive of all taxes' under Rule 6(1)(e)"
            }

        return {
            "raw_value": text,
            "normalized_value": None,
            "is_valid_format": False,
            "status": "NOT_DETECTED"
        }

    def parse_net_quantity(self, text: str) -> Dict[str, Any]:
        """
        Parses Net Quantity and normalizes units:
        0.5 kg -> 500 g
        1 kg -> 1000 g
        1000 ml -> 1 L
        """
        cleaned = text.lower().replace(",", "")
        # Guard against nutritional panel confusion: if line contains carb/energy/protein, discard
        if any(w in cleaned for w in ["energy", "protein", "carbohydrate", "sugar", "fat", "kcal", "sodium", "approx"]):
            # Try to locate statutory net qty snippet within
            m = re.search(r"(?:net\s*qty|net\s*quantity|net\s*wt|net\s*weight)\s*[:.\-]?\s*(\d+(?:\.\d+)?)\s*([a-z]+)", cleaned)
            if not m:
                return {
                    "raw_value": text,
                    "normalized_value": None,
                    "is_valid_format": False,
                    "status": "REQUIRES_MANUAL_REVIEW",
                    "review_reason": "Text appears to be from a nutritional facts table rather than the statutory Net Quantity declaration."
                }

        qty_match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)", cleaned)
        if qty_match:
            raw_num = float(qty_match.group(1))
            raw_unit = qty_match.group(2).lower()

            # Normalization logic
            norm_val = raw_num
            norm_unit = raw_unit

            if raw_unit in ["kg", "kilogram", "kilograms"]:
                if raw_num < 1.0:
                    norm_val = round(raw_num * 1000.0, 1)
                    norm_unit = "g"
                else:
                    norm_val = round(raw_num * 1000.0, 1)
                    norm_unit = "g"
            elif raw_unit in ["g", "gm", "gms", "gram", "grams"]:
                if raw_num >= 1000.0 and raw_num % 1000 == 0:
                    norm_val = round(raw_num / 1000.0, 2)
                    norm_unit = "kg"
                else:
                    norm_unit = "g"
            elif raw_unit in ["l", "ltr", "litre", "litres"]:
                norm_val = round(raw_num * 1000.0, 1)
                norm_unit = "ml"
            elif raw_unit in ["ml", "millilitre", "millilitres"]:
                if raw_num >= 1000.0 and raw_num % 1000 == 0:
                    norm_val = round(raw_num / 1000.0, 2)
                    norm_unit = "L"
                else:
                    norm_unit = "ml"
            elif raw_unit in self.COUNT_UNITS:
                norm_unit = "units"

            is_valid_unit = (
                norm_unit in ["g", "kg", "mg", "ml", "L", "units"] or 
                raw_unit in self.WEIGHT_UNITS or 
                raw_unit in self.VOLUME_UNITS or 
                raw_unit in self.COUNT_UNITS
            )

            return {
                "raw_value": text,
                "normalized_value": {
                    "value": norm_val,
                    "unit": norm_unit,
                    "original_unit": raw_unit,
                    "original_value": raw_num
                },
                "is_valid_format": is_valid_unit,
                "status": "VERIFIED" if is_valid_unit else "REQUIRES_MANUAL_REVIEW"
            }

        return {
            "raw_value": text,
            "normalized_value": None,
            "is_valid_format": False,
            "status": "NOT_DETECTED"
        }

    def parse_date(self, text: str, is_mfg: bool = True) -> Dict[str, Any]:
        """
        Parses manufacturing or packing date (Month and Year under Rule 6(1)(d)).
        """
        date_pattern = r"(0[1-9]|1[0-2])[\/\.\-](202\d|2\d)"
        match = re.search(date_pattern, text)
        if match:
            month = int(match.group(1))
            year_str = match.group(2)
            year = int(f"20{year_str}" if len(year_str) == 2 else year_str)
            return {
                "raw_value": text,
                "normalized_value": {
                    "month": f"{month:02d}",
                    "year": year,
                    "formatted": f"{month:02d}/{year}"
                },
                "is_valid_format": True,
                "status": "VERIFIED"
            }

        # Check for month names like "AUG 2026" or "August 2026"
        month_names = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\.\-\/]+(202\d|2\d)"
        m_name = re.search(month_names, text, re.IGNORECASE)
        if m_name:
            return {
                "raw_value": text,
                "normalized_value": {
                    "month": m_name.group(1).upper(),
                    "year": int(m_name.group(2) if len(m_name.group(2)) == 4 else f"20{m_name.group(2)}"),
                    "formatted": f"{m_name.group(1).upper()}/{m_name.group(2)}"
                },
                "is_valid_format": True,
                "status": "VERIFIED"
            }

        return {
            "raw_value": text,
            "normalized_value": None,
            "is_valid_format": False,
            "status": "REQUIRES_MANUAL_REVIEW" if text != "N/A" else "NOT_DETECTED"
        }

    def parse_best_before(self, text: str) -> Dict[str, Any]:
        """
        Parses Best Before / Expiry declaration.
        """
        duration_pattern = r"(\d+|one|two|three|four|five|six|eight|nine|twelve|eighteen|twenty\s*four)\s*(months?|days?|years?)"
        m = re.search(duration_pattern, text, re.IGNORECASE)
        if m:
            return {
                "raw_value": text,
                "normalized_value": {
                    "duration": m.group(1).lower(),
                    "unit": m.group(2).lower(),
                    "type": "duration"
                },
                "is_valid_format": True,
                "status": "VERIFIED"
            }
        date_res = self.parse_date(text, is_mfg=False)
        if date_res["is_valid_format"]:
            return {
                "raw_value": text,
                "normalized_value": date_res["normalized_value"],
                "is_valid_format": True,
                "status": "VERIFIED"
            }

        return {
            "raw_value": text,
            "normalized_value": None,
            "is_valid_format": len(text) > 5,
            "status": "VERIFIED" if len(text) > 5 else "NOT_DETECTED"
        }

    def parse_consumer_care(self, text: str) -> Dict[str, Any]:
        """
        Extracts phone numbers, email addresses, and postal addresses from consumer care declarations.
        Guards against barcodes being mistaken for helpline numbers.
        """
        email_match = re.search(r"[\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}", text)
        email = email_match.group(0) if email_match else None

        # Toll-free 1800 or standard landline/mobile helpline
        phone_match = re.search(r"(?:1800[-\s]?[0-9]{3,4}[-\s]?[0-9]{3,4}|\+?91[-\s]?[6-9]\d{9}|0\d{2,4}[-\s]?\d{6,8})", text)
        phone = phone_match.group(0) if phone_match else None

        # If only an unlabelled 9-13 digit number without keywords is found, it's likely a barcode or batch!
        if not phone and not email:
            barcode_like = re.search(r"\b\d{9,14}\b", text)
            if barcode_like:
                return {
                    "raw_value": text,
                    "normalized_value": None,
                    "is_valid_format": False,
                    "status": "REQUIRES_MANUAL_REVIEW",
                    "review_reason": "Numeric string detected appears to be an EAN/UPC barcode rather than statutory helpline contact."
                }

        has_contact = bool(email or phone or "care" in text.lower() or "helpline" in text.lower())
        return {
            "raw_value": text,
            "normalized_value": {
                "helpline_phone": phone,
                "email": email,
                "has_contact_means": has_contact
            },
            "is_valid_format": has_contact,
            "status": "VERIFIED" if has_contact else "REQUIRES_MANUAL_REVIEW"
        }

    def parse_unit_sale_price(self, text: str) -> Dict[str, Any]:
        """
        Parses Unit Sale Price (e.g. 'Rs 0.25 / g' or 'Rs 52.00 per kg').
        """
        m = re.search(r"(?:\u20b9|Rs\.?|INR)?\s*(\d+(?:\.\d{1,4})?)\s*(?:per|\/)\s*([a-zA-Z]+)", text, re.IGNORECASE)
        if m:
            price = float(m.group(1))
            unit = m.group(2).lower()
            return {
                "raw_value": text,
                "normalized_value": {
                    "price": price,
                    "base_unit": unit
                },
                "is_valid_format": True,
                "status": "VERIFIED"
            }
        return {
            "raw_value": text,
            "normalized_value": None,
            "is_valid_format": False,
            "status": "REQUIRES_MANUAL_REVIEW" if text != "N/A" else "NOT_DETECTED"
        }

    def parse_country_of_origin(self, text: str) -> Dict[str, Any]:
        """
        Strips export territory statements ('For sale in India, Nepal, Bhutan') to extract true origin.
        """
        sanitized = re.sub(r"for\s*sale\s*(?:only)?\s*in\s*[^.\n]+", "", text, flags=re.IGNORECASE)
        sanitized = re.sub(r"marketed\s*in\s*[^.\n]+", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"export\s*(?:to)?\s*[^.\n]+", "", sanitized, flags=re.IGNORECASE)

        m = re.search(r"(?:made\s*in|product\s*of|mfd\s*in|origin\s*[:.\-]?)\s*([A-Za-z\s]{3,20})", sanitized, re.IGNORECASE)
        if m:
            origin_country = m.group(1).strip().title()
        else:
            words = [w.title() for w in sanitized.split() if len(w) >= 3 and w.lower() not in ["the", "and", "product", "packaged", "origin"]]
            origin_country = words[0] if words else "India"

        return {
            "raw_value": text,
            "normalized_value": {
                "country": origin_country
            },
            "is_valid_format": True,
            "status": "VERIFIED"
        }

    def parse_manufacturer(self, text: str) -> Dict[str, Any]:
        """
        Validates manufacturer, packer or importer statutory address.
        """
        has_pincode = bool(re.search(r"\b\d{6}\b", text))
        has_keywords = bool(re.search(r"(?:mfg|mfr|manufactured|packed|marketed|ltd|pvt|limited|road|street|nagar|plot|industrial)", text, re.IGNORECASE))
        is_complete = has_keywords and (has_pincode or len(text) > 25)

        return {
            "raw_value": text,
            "normalized_value": {
                "address": text,
                "has_pincode": has_pincode
            },
            "is_valid_format": is_complete,
            "status": "VERIFIED" if is_complete else "REQUIRES_MANUAL_REVIEW",
            "review_reason": None if is_complete else "Manufacturer address may lack postal PIN code or complete registered location."
        }

    def parse_product_or_brand(self, text: str, field: str) -> Dict[str, Any]:
        is_valid = bool(text and len(text.strip()) >= 2 and text.strip().lower() != "n/a")
        return {
            "raw_value": text,
            "normalized_value": {"name": text.strip()},
            "is_valid_format": is_valid,
            "status": "VERIFIED" if is_valid else "NOT_DETECTED"
        }

field_parser = FieldParser()
