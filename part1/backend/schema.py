from pydantic import BaseModel

class Date(BaseModel):
    day: str = ""
    month: str = ""
    year: str = ""

class Address(BaseModel):
    street: str = ""
    houseNumber: str = ""
    entrance: str = ""
    apartment: str = ""
    city: str = ""
    postalCode: str = ""
    poBox: str = ""

class MedicalInstitutionFields(BaseModel):
    healthFundMember: str = ""
    natureOfAccident: str = ""
    medicalDiagnoses: str = ""

class InjuryForm(BaseModel):
    lastName: str = ""
    firstName: str = ""
    idNumber: str = ""
    gender: str = ""
    dateOfBirth: Date = Date()
    address: Address = Address()
    landlinePhone: str = ""
    mobilePhone: str = ""
    jobType: str = ""
    dateOfInjury: Date = Date()
    timeOfInjury: str = ""
    accidentLocation: str = ""
    accidentAddress: str = ""
    accidentDescription: str = ""
    injuredBodyPart: str = ""
    signature: str = ""
    formFillingDate: Date = Date()
    formReceiptDateAtClinic: Date = Date()
    medicalInstitutionFields: MedicalInstitutionFields = MedicalInstitutionFields()
