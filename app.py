from langchain_community.chat_models import ChatDeepInfra
import os
from langchain_core.prompts import PromptTemplate
from prompts import question_maker_prompt
import PyPDF2
import time
import streamlit as st
from fpdf import FPDF
######################################################
# THIS SPACE IS FOR DEFINING THE FUNCTIONS
######################################################

def extract_chapter_name(text):
  """Extracts the chapter name from a formatted string.

  Args:
    text: The input string.

  Returns:
    The extracted chapter name.
  """

  # Assuming chapter name ends before the first digit
  for i, char in enumerate(text):
    if char.isdigit():
      return text[:i]

def generate_pdf(text, grade, subject, chapter, difficulty, question_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add header information with formatting
    pdf.set_font("Arial", size=14, style='B')
    pdf.cell(0, 10, f"Grade: {grade}", ln=1, align='L')
    pdf.cell(0, 10, f"Subject: {subject}", ln=1, align='L')
    pdf.cell(0, 10, f"Chapter: {chapter}", ln=1, align='L')
    pdf.cell(0, 10, f"Difficulty Level: {difficulty}", ln=1, align='L')
    pdf.cell(0, 10, f"Question Type: {question_type}", ln=1, align='L')
    pdf.ln(10)  # Add some spacing

    # Add the main text
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)

    pdf_data = pdf.output(dest='S').encode('latin-1')
    return pdf_data



def extract_text(pdf_file):
  with open(pdf_file, 'rb') as pdf_reader:
    reader = PyPDF2.PdfReader(pdf_reader)
    text = ""
    for page_num in range(len(reader.pages)):
      page = reader.pages[page_num]
      text += page.extract_text()
    return text
  


def stream_string(string):
    for char in string:
        yield char
        time.sleep(0.00000005)  # Adjust delay as needed

  
############################################################################
# LLM DEFINITION
temparature =0.5
repetition_penalty = 1.1
max_new_tokens =8096
top_p = 0.9



# DEEPINFRA MISTRAL INSTRUCT V0.3 
DeepInfra_mistral_inst_7b_3 = ChatDeepInfra(
    verbose=True,
    model="mistralai/Mistral-7B-Instruct-v0.3"
)


DeepInfra_mistral_inst_7b_3.model_kwargs = {
    "temperature": temparature,
    "repetition_penalty": repetition_penalty,
    "max_tokens": max_new_tokens,
    "top_p": top_p,
    "max_retries" : 2}


#############################################################################
# STREAMLIT APP

st.set_page_config(initial_sidebar_state ="expanded",
                   page_title="Q&A Generator", 
                   page_icon=":hamster:",
                   layout='wide' )

st.title("QUESTION SET GENERATOR")


st.sidebar.header("SELECTION MENU")


######################################
# Dropdown menu
grade = st.sidebar.selectbox(
    "GRADE",
    ("class 7", "class 8")
)

# Dropdown menu
subject = st.sidebar.selectbox(
    "SUBJECT",
    ("science","science")
)




# slider menu
chapter = st.sidebar.slider("CHAPTER NUMBER", min_value=1, max_value=13)

# defining the file path
file_path = os.path.join('documents',f'{grade}',f'{subject}',f'{chapter}.pdf')

# write the chapter name in the sidebar
st.sidebar.write(fr"CHAPTER : {extract_chapter_name(extract_text(file_path))[:40]}")


# Dropdown menu
difficulty = st.sidebar.selectbox(
    "DIFFICULTY LEVEL",
    ("EASY", "MODERATE","TOUGH","VERY TOUGH")
)


# Dropdown menu
question_type = st.sidebar.selectbox(
    "QUESTION TYPE",
("ASSERTION AND REASON QUESTIONS", "CASE STUDY : CONTEXT WITH QUESTIONS", "DIAGRAM QUESTIONS", "FILL IN THE BLANKS",
 "GUESS WHO AM I?", "LONG QUESTIONS", "MATCH THE FOLLWING", "MCQ QUESTIONS", 
 "ONE WORD QUESTIONS", "REASONING QUESTIONS", "TRUE OR FALSE", "VERY SHORT QUESTIONS"))


# Dropdown menu
with_answers = st.sidebar.selectbox(
    "ANSWERS REQUIRED?",
    ("YES", "NO")
)


# slider to select no of question to be generated
no_of_questions = st.sidebar.slider("SELECT NO OF QUESTIONS TO BE GENERATED", min_value=1, max_value=20)

##################################################################################



#load the data of the pdf file 
context = extract_text(file_path)
    
# Generation logic


if st.button("GENERATE"):
    with st.spinner("**GENERATING THE QUESTION SET .....**"):
        prompt_schema = PromptTemplate(
            input_variables=['context', 'difficulty', 'grade', 'no_of_questions', 'question_type', 'subject', 'with_answers'],
            template=question_maker_prompt
        )
        
        prompt = prompt_schema.format(
            context=context,
            difficulty=difficulty,
            grade=grade,
            no_of_questions=no_of_questions,
            question_type=question_type,
            subject=subject,
            with_answers=with_answers
        )

        response = DeepInfra_mistral_inst_7b_3.invoke(prompt)
        output_content = response.content
        # st.write_stream(stream_string(output_content)) # use this for stream effect
        st.write(output_content)

        cost_usd = response.response_metadata.get('token_usage').get('estimated_cost') 
        st.write(f":green[**Response Cost Estimate = ₹ {83.52*cost_usd}**]")

        # downloading text as pdf
        pdf_data = generate_pdf(output_content, grade, subject, chapter, difficulty, question_type)
        st.download_button(
            label=":blue[**Download PDF**]",
            data=pdf_data,
            file_name=f"class{grade}_{subject}_ch{chapter}_{question_type}_Q{no_of_questions}_{with_answers}.pdf",
            mime='application/pdf'
        )
