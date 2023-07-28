import spacy
from spacy.matcher import Matcher

import langcodes
import re
import pandas as pd

import csv
from datetime import date, datetime
from rapidfuzz import process, fuzz
# create global variable to hold extracted data
extracted_text = {}

# load pre-trained model
nlp = spacy.load("en_core_web_sm")

# initialize matcher with a vocab
matcher = Matcher(nlp.vocab)

month_abbr = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
month_name = ['january','february','march','april','may','june','july','august','september','october', 'november','december']
month_name2 = ['01', '02','03','04','05','06','07','08','09','10','11','12']

def open_file(file_name):
    filename = file_name
    job_file = open(filename, 'r')
    reader = csv.reader(job_file)
    job_list = []
    for row in reader:
        job_list.append(''.join(row))
    return job_list

job_list_specalist = open_file("src/notebooks/support/job_specalist.txt")


# Convert data duration
def convert_date_duration(date_string):
    months = 0
    #word =  date_string.split()
    word =  date_string.split() 
    
    index_month = []
    index_year = []
    setup_date = False

    try:
        for i in range(len(word)):
            
            feature = word[i].lower()
            if feature in month_abbr:
                index_month.append(month_abbr.index(feature)+1)

            if feature in month_name:
                index_month.append(month_name.index(feature)+1)
            
            if feature in month_name2:
                index_month.append(month_name2.index(feature)+1)
            

            x_match = re.match("(202|201)",feature)
            if x_match:
                index_year.append(feature)
            
            if feature == "present" or feature == "now" or feature == "current":
                setup_date = True


        todays_date = datetime.now()


        if len(index_year) == 2 and setup_date == False:
            date1 = date(int(index_year[0]), index_month[0], 1)
            date2 = date(int(index_year[1]), index_month[1], 1)

        if setup_date == True:
            date1 = date(int(index_year[0]), index_month[0], 1)
            date2 = date(todays_date.year, todays_date.month, todays_date.day)
            #date2 = date(todays_date.year, todays_date.month)

        try:
            delta = date2 - date1
            #print("Difference: ", delta.days)
            number_of_days = delta.days
            # Calculating years
            #years = number_of_days // 365
            # Calculating months
            months = number_of_days // 30
            #print(months)
        except:
            pass
        
        return date1,date2,months
    except:
        return "","",0

#match job
def match_job(block_job,job_list):
    job_score = {}
    job_title = ""
    for job_string in block_job:
        score =  process.extractOne(job_string.lower(), job_list)
        if score[1] >= 86:
          job_score[job_string] = score
          job_title = job_string

    
    return job_title

#extract exp
def extract_experience(resume_text):

    block_final = {}

    x_match_start = re.search("EXPERIENCE|EXPERIENCES|Experience|Experiences",resume_text)
    start_index = x_match_start.start()

    regex_stop = "EDUCATION|PROJECTS|SKILLS|ORGANIZATIONS|INVOLVEMENT|CERTIFICATES|ACHIEVEMENTS|Education|Projects|Skills|Organizations|Certificates|Achievements"
    x_match_stop = re.search(regex_stop,resume_text[start_index:len(resume_text)])
    stop_index = x_match_stop.end()

    experience = resume_text[start_index:stop_index]

    # Remove leading and trailing whitespace
    text2 = experience.strip()

    # Split the text into a list of substrings
    substrings = text2.split("\n")

    # Remove empty strings and strip leading/trailing whitespace
    substrings = [s.strip() for s in substrings if s]

    index_start = []
    index_stop = []
    for i,sub_block in enumerate(substrings):
      sub_block_date = sub_block.lower().replace('\n'," ")
      x_match=re.search("^.*20.*(-|–).*(20\d\d|present|now|current)",sub_block_date)
      if x_match:
        index_start.append(i)
      else:
        pass
    

    block_exp = {}
    for z,x in enumerate(index_start):
      try:
        block_exp[z] = substrings[int(index_start[z]):int(index_start[z+1])]
      except:
        block_exp[z] = substrings[int(index_start[z]):int(len(substrings))]
        pass
      
    
    
    block_final["raw"] = block_exp
    block_output = {}
    
    block_job = {}
    block_date = {}
    for r in range(len(block_exp)):

      jobordate = [word for word in block_exp[r] if len(word.split()) < 10]
      job_title = match_job(jobordate,job_list_specalist)
      block_job[r] = job_title

      start_date, end_date, duration = convert_date_duration(block_exp[r][0])
      date = {"start_date":start_date,
                  "end_date":end_date,
                  "duration":duration}
      block_date[r] = date

      block_output[r] = {"job_title" : job_title,
                         "start_date": start_date,
                         "end_date" : end_date,
                         "duration" : duration}
    
    block_final["job"] = block_job
    block_final["date"] = block_date

    return block_output



# define function to extract name from text
def extract_name(resume_text):
    nlp_text = nlp(resume_text)
    # First name and Last name are always Proper Nouns
    pattern = [{"POS": "PROPN"}, {"POS": "PROPN"}]
    matcher.add("NAME", [pattern], on_match=None)
    matches = matcher(nlp_text)
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text


# extract email
def extract_email(string):
    r = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    return r.findall(string)


# extract phone number
def extract_phone_number(string):
    r = re.compile(r"(\b\d{8,}\b)")
    phone_numbers = r.findall(string)
    return [re.sub(r"\D", "", num) for num in phone_numbers]


# extract skils
def extract_skills(resume_text):
    nlp_text = nlp(resume_text)

    # removing stop words and implementing word tokenization
    tokens = [token.text for token in nlp_text if not token.is_stop]

    # reading the csv file
    data = pd.read_csv(
        "src/notebooks/support/skills.csv"
    )

    # extract values
    skills = list(data.columns.values)

    skillset = []

    # check for one-grams (example: python)
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)

    # check for bi-grams and tri-grams (example: machine learning)
    for chunk in nlp_text.noun_chunks:
        chunk_text = chunk.text.lower().strip()
        if chunk_text in skills:
            skillset.append(chunk_text)

    return [i.capitalize() for i in set([i.lower() for i in skillset])]


# get urlLinkedin
def get_urlLinkedin(string):
    pattern = re.compile(r"\b(?:https?://)?(?:www\.)?linkedin\.com/\S+\b")
    return pattern.findall(string)


# extract languages
# def extract_languages(text):
#     isReliable, textBytesFound, details = cld2.detect(text)
#     languages = [
#         lang[1] for lang in details if lang[3] > 0
#     ]  # Filter out languages with zero confidence
#     countries = [langcodes.Language(lang).language_name() for lang in languages]
#     return countries


# extract university
# file = "/home/braiyenmassora/codex-telkom/resume-parser/src/notebooks/support/university.csv"


def extract_university(text, file):
    df = pd.read_csv(file, header=None)
    universities = [i.lower() for i in df[1]]
    college_name = []
    listex = universities
    listsearch = [text.lower()]

    for i in range(len(listex)):
        for ii in range(len(listsearch)):
            if re.findall(listex[i], re.sub(" +", " ", listsearch[ii])):
                college_name.append(listex[i])

    doc = nlp(text)

    # Extract location
    location = ""
    for ent in doc.ents:
        if ent.label_ == "GPE":
            location = ent.text
            break

    # Extract GPA
    gpa = ""
    for match in re.findall(r"GPA: (\d\.\d{2})", text):
        gpa = match
        break

    # Extract faculty and other information
    faculty = ""
    faculty_match = re.search(r"Bachelor of [a-zA-Z ]+ \d{4}-\d{4}", text)
    if faculty_match:
        faculty = faculty_match.group(0)
        other_info = text[faculty_match.end() :].strip()

    # Extract date
    date = ""
    for ent in doc.ents:
        if ent.label_ == "DATE":
            date = ent.text
            break

    return (
        college_name,
        location,
        gpa,
        faculty,
        date,
    )


# extract certifications
def extract_certifications(resume_text):
    nlp_text = nlp(resume_text)

    matcher = Matcher(nlp.vocab)
    pattern = [
        {"LOWER": {"IN": ["certification", "certifications", "license"]}},
        {"IS_PUNCT": True, "OP": "?"},
        {
            "ENT_TYPE": {
                "NOT_IN": [
                    "",
                    "PERSON",
                    "NORP",
                    "FAC",
                    "GPE",
                    "LOC",
                    "PRODUCT",
                    "EVENT",
                    "WORK_OF_ART",
                    "LAW",
                    "LANGUAGE",
                    "DATE",
                    "TIME",
                    "PERCENT",
                    "MONEY",
                    "QUANTITY",
                    "ORDINAL",
                    "CARDINAL",
                ]
            }
        },
    ]
    matcher.add("CERT_ORG", None, pattern)

    matches = matcher(nlp_text)

    certifications = []
    for match_id, start, end in matches:
        cert_org = nlp_text[start:end].text.strip().replace("-", " ")
        title = re.search(r"\b[\w\s]+(?=\sCertificate\b)", cert_org)
        organization = re.search(r"(?<=Certificate\s–\s)[\w\s]+", cert_org)
        if title and organization:
            certifications.append(
                {
                    "title": title.group().strip(),
                    "organization": organization.group().strip(),
                }
            )
        elif title:
            certifications.append({"title": title.group().strip(), "organization": ""})
        elif organization:
            certifications.append(
                {"title": "", "organization": organization.group().strip()}
            )

    return certifications


# extract portfolioLinkUrl
def extract_portfolioLinkUrl(resume_text):
    nlp_text = nlp(resume_text)
    matcher = Matcher(nlp.vocab)
    pattern = [
        {"LOWER": "github"},
        {"IS_PUNCT": True, "OP": "?"},
        {"LOWER": "com"},
        {"IS_PUNCT": True, "OP": "?"},
        {"LOWER": {"IN": ["/", "user", "org"]}},
        {"IS_PUNCT": True, "OP": "?"},
        {"LOWER": {"REGEX": "[a-zA-Z0-9_-]+"}},
        {"IS_PUNCT": True, "OP": "?"},
        {"LOWER": {"REGEX": "(repos|tree|blob|issues|pull)"}, "OP": "?"},
        {"IS_PUNCT": True, "OP": "?"},
        {"LOWER": {"REGEX": "[a-zA-Z0-9/._-]+"}},
    ]
    matcher.add("PORTFOLIO", None, pattern)
    matches = matcher(nlp_text)
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text
