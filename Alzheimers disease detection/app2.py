import streamlit as st
import tensorflow as tf
from PIL import Image
import numpy as np
from streamlit_option_menu import option_menu
import re
import base64
from fpdf import FPDF
import time
import mysql.connector

# Connect to the MySQL database
try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Password",
        database="alzheimers"
    )
    print("Database connection successful")
except mysql.connector.Error as err:
    print("Error connecting to database:", err)
    exit(1)
# Get a cursor object to execute SQL queries
mycursor = mydb.cursor()

create_table_sql = """
CREATE TABLE IF NOT EXISTS predictions (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Patient_Name VARCHAR(255),
    Age INT,
    Gender VARCHAR(10),
    Contact VARCHAR(15),
    Prediction VARCHAR(50)
);
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
"""

# Execute the SQL command to create the table
try:
    mycursor.execute(create_table_sql)
    mycursor.close()
    print("Table created successfully")
except mysql.connector.Error as err:
    print("Error creating table:", err)


st.markdown("""
<style>
    button.step-up {display: none;}
    button.step-down {display: none;}
    div[data-baseweb] {border-radius: 4px;}
</style>""",
unsafe_allow_html=True)

# Define the register function
def register(username, password):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Password",
            database="alzheimers"
        )
        print("Database connection successful")
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        exit(1)
    try:
        sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
        val = (username, password)
        mycursor = mydb.cursor()
        mycursor.execute(sql, val)
        mydb.commit()  # Commit the transaction
        mycursor.close()
        print("User registered successfully")
        return True
    except mysql.connector.Error as err:
        print("Error registering user:", err)
        return False



# Define the login function
def login(username, password):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Password",
            database="alzheimers"
        )
        print("Database connection successful")
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        exit(1)
    try:
        sql = "SELECT * FROM users WHERE username = %s AND password = %s"
        val = (username, password)
        mycursor = mydb.cursor()
        mycursor.execute(sql, val)
        user = mycursor.fetchone()
        mydb.commit()  # Commit the transaction
        mycursor.close()
        if user:
            return True
        else:
            return False
    except mysql.connector.Error as err:
        print("Error executing SQL query:", err)
        return False


def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(username, password):
            st.success("Login successful")
            return True
        else:
            st.error("Invalid username or password")
            return False


def register_page():
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Register"):
        if password == confirm_password:
            if register(username, password):
                st.success("Registration successful")
                return True
            else:
                st.error("Error registering user")
                return False
        else:
            st.error("Passwords do not match")
            return False
        

def main():
    st.sidebar.title("Navigation")
    menu_selection = st.sidebar.radio("Go to", ["Login", "Register"])
    session_state = st.session_state

    # Check if 'is_authenticated' key exists in session state
    if 'is_authenticated' not in session_state:
        # If not, initialize it to False
        session_state.is_authenticated = False

    # Check if 'last_active_time' key exists in session state
    if 'last_active_time' not in session_state:
        # If not, initialize it to current time
        session_state.last_active_time = time.time()

    # Check if session timeout has occurred (more than 5 minutes of inactivity)
    if time.time() - session_state.last_active_time > 300:
        # Reset authentication status and last active time
        session_state.is_authenticated = False
        session_state.last_active_time = time.time()

    if menu_selection == "Login":
        if session_state.is_authenticated:
            # If already authenticated, redirect to appropriate section
            redirect_to_selected_section()
        elif login_page():
            session_state.is_authenticated = True
            session_state.last_active_time = time.time()  # Update last active time
            st.sidebar.success("Logged in successfully")
            show_alzheimer_detection_section()
    elif menu_selection == "Register":
        if session_state.is_authenticated:
            # If already authenticated, redirect to appropriate section
            redirect_to_selected_section()
        elif register_page():
            session_state.is_authenticated = True
            session_state.last_active_time = time.time()
            st.sidebar.success("Registration successful")
            redirect_to_selected_section()


def redirect_to_selected_section():
    if selected == "Alzhiemer Detection":
        show_alzheimer_detection_section()


def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-position: center;
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)
set_background('.\images\\bg.jpg')

# Load the saved model
model = tf.keras.models.load_model('C:\\Users\\suhas\\Downloads\\Alzheimers disease detection (1)\\Alzheimers disease detection\\my_model.h5')

# Define the class labels
class_labels = ['Mild Demented', 'Moderate Demented',
                'Non Demented', 'Very Mild Demented']

# Define the function to preprocess the image


def preprocess_image(image):
    image = image.convert('RGB')
    image = image.resize((176, 176))
    image = np.array(image)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    return image

# Define the Streamlit app

def validate_phone_number(phone_number):
    """
    Validates that a phone number is a 10-digit number.
    """
    pattern = r'^\d{10}$'
    contact=re.match(pattern, str(phone_number))
    if not contact:
        st.error('Please enter a 10 digit number!')
        return False
    return True

def validate_name(name):
    if not all(char.isalpha() or char.isspace() for char in name):
        st.error("Name should not contain numbers or special character.")
        return False
    return True

def validate_input(name, age,contact,file):
    if not name:
        st.error('Please enter the patients name!')
        return False
    if not age:
        st.error('Please enter your age!')
        return False
    if not contact:
        st.error('Please enter your contact number!')
        return False
    if not file:
        st.error('Please upload the MRi Scan!')
        return False
    return True
def is_mri_image(image):
    # Convert the image to a numpy array
    img_array = np.array(image)

    if len(img_array.shape) == 2 or np.var(img_array) < 100:
        return True
    else:
        st.error('Please upload a valid brain MRI image!')
        return False
#with st.sidebar:
selected = option_menu(
            menu_title=None,  # required
            options=["Alzhiemer Detection"],  # required
            icons=["book"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )

def show_alzheimer_detection_section():
    st.title('Alzheimer Detection Web App')
    st.write('Please enter your personal details along with MRI scan.')

    # Add fields for name, age, contact, and gender
    with st.form(key='myform', clear_on_submit=True):
        name = st.text_input('Name')
        age = st.number_input('Age', min_value=1, max_value=150, value=40)
        gender = st.radio('Gender', ('Male', 'Female','Other'))
        contact = st.text_input('Contact Number', value='', key='contact')

        file = st.file_uploader('Upload an image', type=['jpg', 'jpeg', 'png'])
        submit=st.form_submit_button("Submit")

        # Define a function to insert the form data into the `prediction` table
    def insert_data(name, age, gender, contact, prediction):
        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Password",
                database="alzheimers"
            )
            print("Database connection successful")
        except mysql.connector.Error as err:
            print("Error connecting to database:", err)
            exit(1)
        try:
          sql = "INSERT INTO predictions (Patient_Name, Age, Gender, Contact, Prediction) VALUES (%s, %s, %s, %s, %s)"
          val = (name, age, gender, contact, prediction)
          mycursor = mydb.cursor()
          mycursor.execute(sql, val)
          mydb.commit()
          mycursor.close()
          print(mycursor.rowcount, "record inserted")
        except mysql.connector.Error as err:
          print("Error inserting record:", err)  

                
    if file is not None and validate_input(name, age,contact,file) and validate_phone_number(contact) and validate_name(name) and is_mri_image(Image.open(file)):
                  st.success('Your personal information has been recorded.', icon="✅")
                  image = Image.open(file)
                  png_image = image.convert('RGBA')
                  st.image(image, caption='Uploaded Image', width=200)
                  # Use the fields for name, age, contact, and gender in the output
        
                  st.write('Name:', name)
                  st.write('Age:', age)
                  st.write('Gender:', gender)
                  st.write('Contact:', contact)
                  image = preprocess_image(image)
                  prediction = model.predict(image)
                  prediction = np.argmax(prediction, axis=1)
                  st.success('The predicted class is: '+ class_labels[prediction[0]])
                  result_str = 'Name: {}\nAge: {}\nGender: {}\nContact: {}\nPrediction for Alzheimer: {}'.format(
                     name, age, gender, contact, class_labels[prediction[0]])
                  insert_data(name, age, gender, contact, class_labels[prediction[0]])
                  export_as_pdf = st.button("Export Report")

                  def create_download_link(val, filename):
                    b64 = base64.b64encode(val)  # val looks like b'...'
                    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download report</a>'
        
                  if export_as_pdf:
                     pdf = FPDF()
                     pdf.add_page()
                     # set the border style
                     pdf.set_draw_color(0, 0, 0)
                     pdf.set_line_width(1)

                     # add a border to the entire page
                     pdf.rect(5.0, 5.0, 200.0, 287.0, 'D')
    
                     # Set font for title
                     pdf.set_font('Times', 'B', 24)
                     pdf.cell(200, 20, 'Alzheimer Detection Report', 0, 1, 'C')
    
                     # Set font for section headers
                     pdf.set_font('Arial', 'B', 16)
                     pdf.cell(200, 10, 'Patient Details', 0, 1)
    
                     # Set font for regular text
                     pdf.set_font('Arial', '', 12)
                     pdf.cell(200, 10, f'Name: {name}', 0, 1)
                     pdf.cell(200, 10, f'Age: {age}', 0, 1)
                     pdf.cell(200, 10, f'Gender: {gender}', 0, 1)
                     pdf.cell(200, 10, f'Contact: {contact}', 0, 1)
                     pdf.ln(0.15)
                     pdf.ln(0.15)



                     # Add the image to the PDF object's images dictionary
                     png_file = "image.png"
                     png_image.save(png_file, "PNG")
                     pdf.cell(200, 10, 'MRI scan:', 0, 1)
                     pdf.image(png_file, x=40, y=80, w=50,h=50)
                     pdf.ln(0.15)
                     pdf.ln(10.0)
                     pdf.ln(10.0)
                     pdf.ln(10.15)
                     pdf.ln(10.15)
                     pdf.ln(1.15)
                     pdf.ln(1.15)
                     pdf.ln(1.15)

                     # Set font for prediction text
                     pdf.set_font('Arial', 'B', 16)
                     pdf.cell(200, 10, f'Prediction for Alzheimer: {class_labels[prediction[0]]}', 0, 1)
                     pdf.ln(2.0)
                     pdf.set_font('Arial', 'B', 12)
                     if (prediction!=2):
                      pdf.set_text_color(255, 0, 0)
                      pdf.cell(200,10,'Demetia detected in your MRI, kindly consult a nearby neurologist immediately!',0,1)
                      pdf.set_text_color(0, 0, 255)
                      pdf.set_font('Arial', 'B', 10)
                      pdf.cell(200, 10, 'Here are some precautions you can take:', 0, 1, 'C')
                      pdf.ln(2)

                      precautions = [
                        '1. Stay mentally active: Engage in mentally stimulating activities such as reading, writing, puzzles, and games to keep your brain active.',
                        '2. Stay physically active: Exercise regularly to improve blood flow to the brain and help prevent cognitive decline.',
                        '3. Eat a healthy diet: Eat a balanced diet that is rich in fruits, vegetables, whole grains, and lean protein to help maintain brain health.',
                        '4. Stay socially active: Engage in social activities and maintain social connections to help prevent social isolation and depression.',
                        '5. Get enough sleep: Aim for 7-8 hours of sleep per night to help improve brain function and prevent cognitive decline.'                ]
        
                      pdf.set_font('Arial', '', 12)

                      for precaution in precautions:
                       pdf.multi_cell(190, 10, precaution, 0, 1, 'L')
                       pdf.ln(1)
          
                     else:
                       pdf.set_text_color(0, 255, 0)
                       pdf.cell(200,10,'Congratulations! There is no sign of demetia in your MRI.',0,1)
    
                      # Create and display the download link
                     html = create_download_link(pdf.output(dest="S").encode("latin-1"), "test")
                     st.markdown(html, unsafe_allow_html=True)


# Run the app
if __name__ == '__main__':
    main()