REQUIRED_FIELDS = [
    "firstName", "lastName", "idNumber", "dateOfBirth", "dateOfInjury"
]

def validate_extraction(data: dict):
    missing = []
    filled = 0
    total = 0

    def count_fields(obj):
        nonlocal filled, total
        for v in obj.values():
            if isinstance(v, dict):
                count_fields(v)
            else:
                total += 1
                if v.strip():
                    filled += 1

    count_fields(data)

    for field in REQUIRED_FIELDS:
        if not data.get(field):
            missing.append(field)

    completeness_score = round((filled / total) * 100, 2)

    return {
        "missing_required_fields": missing,
        "completeness_score_percent": completeness_score
    }
