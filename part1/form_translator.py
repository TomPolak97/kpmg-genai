import logging
from typing import Dict

# ------------------ Setup logging ------------------
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

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
            raise TypeError(f"Expected a dict for data, got {type(data)}")

        if language.lower() == "english":
            logger.info("Language is English; no translation needed.")
            return data  # no translation needed

        mapping = LANGUAGE_MAPPINGS.get(language.lower())
        if not mapping:
            raise ValueError(f"Unsupported language: {language}")

        def _translate(d: dict) -> dict:
            new_d = {}
            for k, v in d.items():
                new_key = mapping.get(k, k)
                if new_key != k:
                    logger.debug("Translating key '%s' -> '%s'", k, new_key)
                else:
                    logger.debug("No translation found for key '%s', keeping original", k)
                if isinstance(v, dict):
                    new_d[new_key] = _translate(v)
                elif isinstance(v, list):
                    # Translate dictionaries inside lists
                    new_list = []
                    for item in v:
                        if isinstance(item, dict):
                            new_list.append(_translate(item))
                        else:
                            new_list.append(item)
                    new_d[new_key] = new_list
                else:
                    new_d[new_key] = v
            return new_d

        translated_data = _translate(data)
        logger.info("Translation to '%s' completed successfully.", language)
        return translated_data

    except Exception as e:
        logger.exception("Failed to translate form")
        # Return original data as a safe fallback
        return data

