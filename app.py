from flask import Flask, render_template, request, redirect, url_for
import os
import random
import psycopg2
from helpers import GBLite2

app = Flask(__name__)

DATABASE_URL = "postgresql://errorspotting_data_user:XRTOlLOmzvAZJi1PEvlH6kYZi1icZEly@dpg-ctr8sol2ng1s73esvf40-a.frankfurt-postgres.render.com/errorspotting_data"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

# Create table if it doesn't exist (you may want to rename it to `user_inputs`)
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS main_db (
            id SERIAL PRIMARY KEY,
            imgId TEXT,
            es_label TEXT,
            hint_label TEXT
        )
    """)
    conn.commit()
print('TABLE CREATED')
conn.close()

# Directory setup
IMAGE_FOLDER = 'static/imagesApp'
PROBLEM_FOLDER = 'static/textApp/problem'
CORRECT_FOLDER = 'static/textApp/correct'
ANSWER_FOLDER = 'static/textApp/answer'
HINT_FOLDER = 'static/textApp/hint'
TRANS_FOLDER = 'static/textApp/trans'
USER_INPUT_FOLDER = 'user_input'
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(PROBLEM_FOLDER, exist_ok=True)
os.makedirs(USER_INPUT_FOLDER, exist_ok=True)

app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['PROBLEM_FOLDER'] = PROBLEM_FOLDER
app.config['CORRECT_FOLDER'] = CORRECT_FOLDER
app.config['ANSWER_FOLDER'] = ANSWER_FOLDER
app.config['HINT_FOLDER'] = HINT_FOLDER
app.config['TRANS_FOLDER'] = TRANS_FOLDER
app.config['USER_INPUT_FOLDER'] = USER_INPUT_FOLDER

@app.route('/')
def home():

    # Get all imgId values from the database
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT imgId FROM main_db")
        existing_ids = [row[0] for row in cur.fetchall()]
        for row in cur.fetchall():
            existing_ids.append(row[0])
    conn.close()

    done_count = len(existing_ids)
    # Count the number of folders in the IMAGE_FOLDER
    all_count = len([f for f in os.listdir(app.config['IMAGE_FOLDER'])])

    # Get a list of all image files in the IMAGE_FOLDER
    image_files = [f for f in os.listdir(app.config['IMAGE_FOLDER'])]

    # Find an img that has not been labelled yet
    imgFound = False

    while imgFound == False:

        # Select a random image
        selected_image_folder = random.choice(image_files)
        selected_image = next(f for f in os.listdir(os.path.join(app.config['IMAGE_FOLDER'], selected_image_folder)) if f.startswith('image_ES'))
        ref_image = next(f for f in os.listdir(os.path.join(app.config['IMAGE_FOLDER'], selected_image_folder)) if f.startswith('ref'))

        image_id = selected_image.rsplit('.', 1)[0]
        # Remove 'image_' prefix from the image ID if it exists
        if image_id.startswith('image_ES'):
            image_id = image_id.split('_')[-1]
        
        if image_id not in existing_ids:
            # Find the corresponding text file
            problem_file = f'problem_{image_id}.txt'  # Replace the image extension with .txt
            problem_path = os.path.join(app.config['PROBLEM_FOLDER'], problem_file)
            # Read the text content (if the file exists)
            if os.path.exists(problem_path):
                with open(problem_path, 'r') as f:
                    problem_content = f.read()
            else:
                problem_content = "NONE"

            trans_file = f'trans_{image_id}.txt'  # Replace the image extension with .txt
            trans_path = os.path.join(app.config['TRANS_FOLDER'], trans_file)

            # Read the text content (if the file exists)
            if os.path.exists(trans_path):
                with open(trans_path, 'r') as f:
                    trans_content = f.read()
            else:
                trans_content = "NONE"
                
            #if 'nan. Problem image' not in problem_content and trans_content != 'X' and ('x' in problem_content or 'ekvation' in problem_content):
            if 'nan. Problem image' not in problem_content and GBLite2(trans_content) == True:
                imgFound = True

    correct_file = f'correct_{image_id}.txt'  # Replace the image extension with .txt
    correct_path = os.path.join(app.config['CORRECT_FOLDER'], correct_file)

    answer_file = f'answer_{image_id}.txt'  # Replace the image extension with .txt
    answer_path = os.path.join(app.config['ANSWER_FOLDER'], answer_file)

    hint_file = f'hint_{image_id}.txt'  # Replace the image extension with .txt
    hint_path = os.path.join(app.config['HINT_FOLDER'], hint_file)

    # Read the text content (if the file exists)
    if os.path.exists(correct_path):
        with open(correct_path, 'r') as f:
            correct_content = f.read()
    else:
        correct_content = "NONE"

    # Read the text content (if the file exists)
    if os.path.exists(answer_path):
        with open(answer_path, 'r') as f:
            answer_content = f.read()
    else:
        answer_content = "NONE"

    # Read the text content (if the file exists)
    if os.path.exists(hint_path):
        with open(hint_path, 'r') as f:
            hint_content = f.read()
    else:
        hint_content = "NONE"

    problem_content = problem_content.replace("\\n", "").replace("\\quad", "").replace("$", "")
    if len(problem_content) == 0:
        problem_content = 'Missing'
    correct_content = f'{correct_content.replace("[", "").replace("]", "").replace("$", "")}'
    answer_content = f'{answer_content.replace("[", "").replace("]", "").replace("$", "")}'

    # Pass the selected image, text content, and image_id to the template
    return render_template('index.html', 
                           image_path=url_for('static', filename=f'imagesApp/{image_id}/{selected_image}'), 
                           image_path_ref=url_for('static', filename=f'imagesApp/{image_id}/{ref_image}'), 
                           done_count = done_count,
                           all_count = all_count-325,
                           problem_content=problem_content,
                           correct_content=correct_content,
                           answer_content=answer_content,
                           hint_content=hint_content,
                           trans_content=trans_content,
                           image_id=image_id)

@app.route('/submit', methods=['POST'])
def handle_user_input():
    """Handle the form submission for start and end inputs."""
    start_input = request.form.get('start_input', '')
    end_input = request.form.get('end_input', '')
    hint_label = request.form.get('hint_label', '')
    image_id = request.form.get('image_id', '')

    # Combine them into one string for storage in the single 'input' column
    es_label = f'{start_input}/{end_input}'

    conn = get_db_connection()
    with conn.cursor() as cur:
        # Insert into whichever table you are actually using (user_inputs or user_inputs_test)
        cur.execute("INSERT INTO main_db (es_label, hint_label, imgId) VALUES (%s, %s, %s)", (es_label, hint_label, image_id))
        conn.commit()

    conn.close()
    return redirect(url_for('home'))

@app.route('/skip', methods=['POST'])
def skip_user_input():
    """Handle the form submission for skipped solutions."""
    image_id = request.form.get('image_id', '')

    # Combine them into one string for storage in the single 'input' column
    final_input = f'X'

    print(final_input)

    conn = get_db_connection()
    with conn.cursor() as cur:
        # Insert into whichever table you are actually using (user_inputs or user_inputs_test)
        cur.execute("INSERT INTO main_db (input, imgId) VALUES (%s, %s)", (final_input, image_id))
        conn.commit()

    conn.close()
    return redirect(url_for('home'))

@app.route('/discard', methods=['POST'])
def discard_user_input():
    """Handle the form submission for skipped solutions."""
    image_id = request.form.get('image_id', '')

    # Combine them into one string for storage in the single 'input' column
    final_input = f'BAD'

    conn = get_db_connection()
    with conn.cursor() as cur:
        # Insert into whichever table you are actually using (user_inputs or user_inputs_test)
        cur.execute("INSERT INTO main_db (es_label, imgId) VALUES (%s, %s)", (final_input, image_id))
        conn.commit()

    conn.close()
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            return "No file part"
        file = request.files['image']
        if file.filename == '':
            return "No selected file"
        if file and file.filename.lower().endswith(('jpg', 'png', 'jpeg', 'gif')):
            filename = file.filename
            file.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/view_inputs')
def view_inputs():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM main_db")
        inputs = cur.fetchall()
    conn.close()
    return render_template('view_inputs.html', inputs=inputs)

if __name__ == '__main__':
    app.run(debug=True)

