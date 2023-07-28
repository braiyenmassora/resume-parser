import io
from fastapi import APIRouter, FastAPI, File, UploadFile
from PyPDF2 import PdfReader
from src.apps.parser import *
import asyncio
import selectors
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# RuntimeError: 'asyncio' module is not available in this context
selector = selectors.SelectSelector()
loop = asyncio.SelectorEventLoop(selector)
asyncio.set_event_loop(loop)


router = APIRouter()


@router.post("/resumeparser/")
async def pdf_to_text(file: UploadFile = File(...)):
    """
    Convert uploaded PDF file to text and return it.
    """
    pdf_reader = PdfReader(io.BytesIO(await file.read()))
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()

    # extract name from text and store in global variable
    name = extract_name(text)
    extracted_text["fullName"] = name
    email = extract_email(text)
    extracted_text["email"] = email
    phone_number = extract_phone_number(text)
    extracted_text["phone_number"] = phone_number
    skills = extract_skills(text)
    extracted_text["skills"] = skills
    linkedinUrl = get_urlLinkedin(text)
    extracted_text["linkedinUrl"] = linkedinUrl
    experience = extract_experience(text)
    # languages = extract_languages(text)
    # extracted_text["languages"] = languages
    college_name, location, gpa, faculty, date = extract_university(
        text,
        "src/notebooks/support/university.csv",
    )
    education = {}
    if college_name:
        education = {
            "organization": college_name[0],
            "location": location,
            "gpa": gpa,
            "faculty": faculty.strip(),
            "date": date,
        }

    extracted_text["educations"] = [education]
    certifications = extract_certifications(text)
    extracted_text["certifications"] = certifications
    portfolioLinkUrl = extract_portfolioLinkUrl(text)
    extracted_text["portfolioLinkUrl"] = portfolioLinkUrl
    return {
        "filename": file.filename,
        "data": {
            "name": name,
            "email": email,
            "phone_number": phone_number,
            "skills": skills,
            "linkedinUrl": linkedinUrl,
            # "languages": languages,
            "educations": extracted_text["educations"],
            "certifications": certifications,
            "portfolioLinkUrl": portfolioLinkUrl,
            "experience" : experience
        },
    }
