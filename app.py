from flask import Flask, render_template, request, redirect, url_for
import os
import random
import psycopg2

app = Flask(__name__)

DATABASE_URL = "postgresql://errorspotting_data_user:XRTOlLOmzvAZJi1PEvlH6kYZi1icZEly@dpg-ctr8sol2ng1s73esvf40-a/errorspotting_data"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_inputs (
            id SERIAL PRIMARY KEY,
            input TEXT NOT NULL
        )
    """)
    conn.commit()
print('TABLE CREATED')
conn.close()

# Directories containing images and text files
IMAGE_FOLDER = 'static/images'
TEXT_FOLDER = 'static/text'
USER_INPUT_FOLDER = 'user_input'
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(TEXT_FOLDER, exist_ok=True)
os.makedirs(USER_INPUT_FOLDER, exist_ok=True)

app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['TEXT_FOLDER'] = TEXT_FOLDER
app.config['USER_INPUT_FOLDER'] = USER_INPUT_FOLDER

@app.route('/')
def home():
    # Get a list of all image files in the IMAGE_FOLDER
    image_files = [f for f in os.listdir(app.config['IMAGE_FOLDER']) if f.endswith(('jpg', 'png', 'jpeg', 'gif'))]

    if not image_files:
        return "No images available. Please upload an image."

    # Select a random image
    selected_image = random.choice(image_files)

    image_id = selected_image.rsplit('.', 1)[0]
    # Find the corresponding text file
    text_file = image_id + '.txt'  # Replace the image extension with .txt
    text_path = os.path.join(app.config['TEXT_FOLDER'], text_file)

    # Read the text content (if the file exists)
    if os.path.exists(text_path):
        with open(text_path, 'r') as f:
            text_content = f.read()
    else:
        text_content = "No description available."

    # Pass the selected image, text content, and image_id to the template
    return render_template('index.html', 
                           image_path=url_for('static', filename=f'images/{selected_image}'), 
                           text_content=text_content,
                           image_id=image_id)


@app.route('/submit', methods=['POST'])
def handle_user_input():
    user_input = request.form.get('user_input', '')
    image_id = request.form.get('image_id', '')
    
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO user_inputs (input) VALUES (%s)", (user_input,))
        conn.commit()
        
        # Verify the insertion
        cur.execute("SELECT * FROM user_inputs ORDER BY id DESC LIMIT 1")
        result = cur.fetchone()
        print(f"Last inserted row: {result}")
    
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
        cur.execute("SELECT * FROM user_inputs")
        inputs = cur.fetchall()
    conn.close()
    return render_template('view_inputs.html', inputs=inputs)

if __name__ == '__main__':
    app.run(debug=True)

