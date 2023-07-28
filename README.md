## Resume Parser

> Resume Parser is a Python library that extracts information from resumes in various file formats such as PDF. It uses natural language processing (NLP) techniques to identify key sections of a resume, such as the candidate's name, contact information, work experience, education, and skills.

### Tech Used

- Python3
- Spacy
- NLP
- fastAPI

### Run Notebook

```bash
  # setup
  git clonehttps://github.com/braiyenmassora/resume-parser.git
  git checkout develop
  cd resume-parser
  source env/bin/activate
  pip install requirements.txt

  # open notebooks dir
  resumeParser.ipynb
  customModel.ipynb

```
### API Testing

```bash
  # setup
  cd resume-parser
  source .env/bin/activate
  pip3 install requirements.txt

  # run this
  uvicorn main:app --reload  [Linux]
  python3 -m uvicorn main:app --reload [MacOs]
  http://127.0.0.1:8000

  # using postman to test
  http://localhost:8000/resumeparser/
```
