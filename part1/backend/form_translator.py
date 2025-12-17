# translator.py
from typing import Dict

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
    # You can add more languages here, e.g., "spanish": { ... }
}


def translate_form(data: dict, language: str) -> dict:
    """
    Recursively translates JSON keys to the target language.
    :param data: dict with English keys
    :param language: language code, e.g., "hebrew"
    :return: dict with translated keys
    """
    if language.lower() == "english":
        return data  # no translation needed

    mapping = LANGUAGE_MAPPINGS.get(language.lower())
    if not mapping:
        raise ValueError(f"Unsupported language: {language}")

    def _translate(d: dict) -> dict:
        new_d = {}
        for k, v in d.items():
            new_key = mapping.get(k, k)
            if isinstance(v, dict):
                new_d[new_key] = _translate(v)
            else:
                new_d[new_key] = v
        return new_d

    return _translate(data)
