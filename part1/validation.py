import logging

# IMPORTANT:
# Logging is configured centrally in logging_config.py
logger = logging.getLogger(__name__)

REQUIRED_FIELDS = [
    "firstName", "lastName", "idNumber", "dateOfBirth", "dateOfInjury"
]


def validate_extraction(data: dict) -> dict:
    """
    Validates the extracted form data.
    Checks for missing required fields and computes a completeness score.

    :param data: dict representing extracted form fields
    :return: dict with missing required fields and completeness score
    """
    try:
        if not isinstance(data, dict):
            raise TypeError(f"Expected data to be a dict, got {type(data)}")

        logger.info("Starting validation of extracted data")

        missing = []
        filled = 0
        total = 0

        def count_fields(obj):
            nonlocal filled, total
            if not isinstance(obj, dict):
                return
            for v in obj.values():
                if isinstance(v, dict):
                    count_fields(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            count_fields(item)
                        else:
                            total += 1
                            if isinstance(item, str) and item.strip():
                                filled += 1
                else:
                    total += 1
                    if isinstance(v, str) and v.strip():
                        filled += 1

        count_fields(data)

        for field in REQUIRED_FIELDS:
            if not data.get(field) or not isinstance(data.get(field), str) or not data.get(field).strip():
                missing.append(field)

        completeness_score = round((filled / total) * 100, 2) if total > 0 else 0.0

        logger.info(
            "Validation completed. Missing fields: %s, Completeness: %.2f%%",
            missing,
            completeness_score
        )

        return {
            "missing_required_fields": missing,
            "completeness_score_percent": completeness_score
        }

    except Exception:
        logger.exception("Validation failed due to an unexpected error")
        return {
            "missing_required_fields": REQUIRED_FIELDS,
            "completeness_score_percent": 0.0,
            "error": "Unexpected validation error"
        }
