import logging
from typing import Dict

# IMPORTANT:
# Logging is configured centrally in logging_config.py.
# We only retrieve a named logger here.
logger = logging.getLogger(__name__)


# Dictionary mapping languages to key mappings
LANGUAGE_MAPPINGS: Dict[str, Dict[str, str]] = {
    "hebrew": {
        "lastName": "שם משפחה",
        "firstName": "שם פרטי",
        "idNumber": "מספר זהות",
        "gender": "מין",
        "dateOfBirth": "תאריך לידה",
        "address": "כתובת",
        "street": "רחוב",
        "houseNumber": "מספר בית",
        "entrance": "כניסה",
        "apartment": "דירה",
        "city": "ישוב",
        "postalCode": "מיקוד",
        "poBox": "תא דואר",
        "landlinePhone": "טלפון קווי",
        "mobilePhone": "טלפון נייד",
        "jobType": "סוג העבודה",
        "dateOfInjury": "תאריך הפגיעה",
        "timeOfInjury": "שעת הפגיעה",
        "accidentLocation": "מקום התאונה",
        "accidentAddress": "כתובת מקום התאונה",
        "accidentDescription": "תיאור התאונה",
        "injuredBodyPart": "האיבר שנפגע",
        "signature": "חתימה",
        "formFillingDate": "תאריך מילוי הטופס",
        "formReceiptDateAtClinic": "תאריך קבלת הטופס בקופה",
        "medicalInstitutionFields": "למילוי ע\"י המוסד הרפואי",
        "healthFundMember": "חבר בקופת חולים",
        "natureOfAccident": "מהות התאונה",
        "medicalDiagnoses": "אבחנות רפואיות",
        "day": "יום",
        "month": "חודש",
        "year": "שנה"
    }
    # Additional languages can be added here
}


def translate_form(data: dict, language: str) -> dict:
    """
    Recursively translates JSON keys to the target language.
    :param data: dict with English keys
    :param language: language code, e.g., "hebrew"
    :return: dict with translated keys
    """
    try:
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for data, got {type(data)}")

        if language.lower() == "english":
            logger.info("Language is English; skipping translation")
            return data

        mapping = LANGUAGE_MAPPINGS.get(language.lower())
        if not mapping:
            raise ValueError(f"Unsupported language: {language}")

        def _translate(d: dict) -> dict:
            translated = {}
            for key, value in d.items():
                new_key = mapping.get(key, key)

                if new_key != key:
                    logger.debug("Translated key '%s' -> '%s'", key, new_key)

                if isinstance(value, dict):
                    translated[new_key] = _translate(value)
                elif isinstance(value, list):
                    translated[new_key] = [
                        _translate(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    translated[new_key] = value

            return translated

        translated_data = _translate(data)
        logger.info("Translation completed successfully (language=%s)", language)
        return translated_data

    except Exception:
        logger.exception("Form translation failed")
        # Safe fallback: return original data
        return data
