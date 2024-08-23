from flask import Flask, render_template, request, session, redirect
from flask_mysqldb import MySQL
import requests
import json
import os
import time
from werkzeug.utils import secure_filename
from PIL import Image
import string
import random
from datetime import datetime, timedelta
import stripe

app = Flask(__name__)

# Configuración de la base de datos MySQL
app.config['SECRET_KEY'] = 'secret!'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'fredy'
app.config['MYSQL_PASSWORD'] = 'fredy'
app.config['MYSQL_DB'] = 'infinityca'
app.config['UPLOAD_FOLDER'] = './static/uploads/'
mysql = MySQL(app)

# Configuración de la clave secreta de Stripe
stripe.api_key = 'tu_clave_secreta_de_stripe'

def can_generate_image(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT last_generation_date, image_generations_remaining FROM users WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    
    if result:
        last_generation_date, remaining_generations = result
        now = datetime.now()

        if last_generation_date:
            time_elapsed = now - last_generation_date
            if time_elapsed < timedelta(days=1):
                if remaining_generations > 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return True

    return False

def update_generation_stats(user_id):
    now = datetime.now()
    cursor = mysql.connection.cursor()
    cursor.execute("""UPDATE users SET last_generation_date = %s, image_generations_remaining = image_generations_remaining - 1 WHERE user_id = %s""", (now, user_id))
    mysql.connection.commit()

def get_user_credits(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT image_generations_remaining FROM users WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0


@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        credits = get_user_credits(user_id)
        return render_template('index.html', credits=credits)
    else:
        return redirect('/login')

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect('/')
    else:
        return render_template('login.html')

@app.route('/register')
def register():
    if 'user_id' in session:
        return redirect('/')
    else:
        return render_template('signup.html')

@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    password = request.form.get('password')
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * FROM `users` WHERE `email` = %s AND `password` = %s""", (email, password))
    user = cursor.fetchone()
    
    if user:
        # Establece la sesión del usuario
        session['user_id'] = user[-1]  # Asumiendo que user_id es el quinto campo en la tabla
        return redirect('/')
    else:
        return redirect('/login')


@app.route('/add_user', methods=['POST'])
def add_user():
    name=request.form.get('name')
    email=request.form.get('email')
    pno=request.form.get('pno')
    password=request.form.get('password')
    gender = request.form.get('gender')
    user_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    cursor = mysql.connection.cursor()
    cursor.execute("""INSERT INTO `users` (`name`, `email`, `pno`, `password`, `user_id`, `gender`) values ("{}","{}","{}","{}","{}","{}")""".format(name,email,pno,password,user_id,gender))
    mysql.connection.commit()
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

def get_prompt_for_gender(user_id, prompttype):
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT gender FROM users WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()

    if result:
        gender = result[0]
        print(f"User ID: {user_id}, Gender retrieved: {gender}")
        if gender == 'male':
            if prompttype == 'linkedin':
               return "Professional portrait of a man, business attire, confident pose, neutral background, studio lighting"
            else:
                return "Man in modern outfit, vibrant colors, natural outdoor lighting, dynamic pose, urban background." 
        elif gender == 'female':
            if prompttype == 'linkedin':            
                return "Professional headshot, business attire, confident pose, neutral background, studio lighting"
            else:
                return 'Trendy outfit, vibrant colors, natural outdoor lighting, dynamic pose, urban background'
        else:
            return "Professional headshot, business attire, confident pose, neutral background, studio lighting"
    
    return "Professional headshot, business attire, confident pose, neutral background, studio lighting"


@app.route('/generate', methods=['POST'])
def generate_image():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    print(f"Session User ID: {user_id}")

    if not can_generate_image(user_id):
        return render_template('index.html', error="You have reached your generation limit for the next 24 hours.")

    api_key = 'Your_API_Key'
    url = "https://api.rendernet.ai/pub/v1/generations"

    facelock_asset_id = None
    
    if 'facelock_image' in request.files:
        facelock_image = request.files['facelock_image']
        if facelock_image.filename != '':
            facelock_asset_id = upload_asset(facelock_image, api_key)

    prompt_type = request.form.get('promptType')
    positive_prompt = get_prompt_for_gender(user_id, prompt_type)
    print(f'prompt {positive_prompt}')
    if prompt_type == 'linkedin':
        negative_prompt = "Casual clothing, busy background, extreme facial expressions"
    elif prompt_type == 'instagram':
        negative_prompt = "Formal attire, plain background, static pose"
    else:
        return render_template('index.html', error="Invalid prompt type")

    payload = json.dumps([
        {
            "aspect_ratio": "1:1",
            "batch_size": 1,
            "cfg_scale": 7,
            "model": "JuggernautXL",
            "prompt": {
                "negative": negative_prompt,
                "positive": positive_prompt
            },
            "quality": "Regular",
            "sampler": "DPM++ 2M Karras",
            "seed": random.randint(1000, 2000),
            "steps": 20,
            "facelock": {"asset_id": facelock_asset_id} if facelock_asset_id else None
        }
    ])
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 202:
        generation_data = response.json()
        print(f"Generation data: {json.dumps(generation_data, indent=2)}")
        image_id = generation_data['data']['images'][0]['id']
        image_url = f"https://redernet-image-data.s3.amazonaws.com/prod/user_generated/user_id/{image_id}.png"
        print(f"Attempting to download image from URL: {image_url}")
        image_path = f"static/{image_id}.png"
        
        if not os.path.exists('static'):
            os.makedirs('static')

        time.sleep(40)

        image_response = requests.get(image_url)
        
        if image_response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            update_generation_stats(user_id)
            credits = get_user_credits(user_id)
            return render_template('generate.html', image_url=image_path, credits=credits)
        else:
            print(f"Failed to download image. Status code: {image_response.status_code}")
            return render_template('index.html', error="Failed to download the generated image.")
    else:
        print(f"Failed to generate image. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return render_template('index.html', error="Failed to generate image")
    
@app.route('/buy_credits')
def buy_credits():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    credits = get_user_credits(user_id)
    return render_template('buy_credits.html', credits=credits)

@app.route('/purchase_credits', methods=['POST'])
def purchase_credits():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    credits_to_add = int(request.form.get('credits', 0))
    amount = credits_to_add * 100  # Stripe trabaja en centavos, así que multiplicamos por 100
    
    # Crear una sesión de pago en Stripe
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'{credits_to_add} Credits',
                },
                'unit_amount': amount,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.host_url + 'payment_success?credits=' + str(credits_to_add),
        cancel_url=request.host_url + 'buy_credits',
    )

    return redirect(session.url, code=303)

@app.route('/payment_success')
def payment_success():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    credits_to_add = int(request.args.get('credits', 0))
    
    # Actualizar los créditos del usuario
    update_user_credits(user_id, credits_to_add)
    
    new_credits = get_user_credits(user_id)
    return render_template('purchase_success.html', credits=new_credits)


def update_user_credits(user_id, credits_to_add):
    cursor = mysql.connection.cursor()
    cursor.execute("""UPDATE users SET image_generations_remaining = image_generations_remaining + %s WHERE user_id = %s""", (credits_to_add, user_id))
    mysql.connection.commit()

def upload_asset(file, api_key):
    request_url = "https://api.rendernet.ai/pub/v1/assets/upload"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    with Image.open(file) as img:
        width, height = img.size
    
    payload = json.dumps({
        "size": {
            "height": height,
            "width": width
        }
    })
    
    response = requests.post(request_url, headers=headers, data=payload)
    print(f"Request URL response: {response.status_code}")
    print(f"Request URL content: {response.text}")
    
    if response.status_code != 200:
        print("Failed to get upload URL")
        return None
    
    response_data = response.json()
    upload_url = response_data['data']['upload_url']
    asset_id = response_data['data']['asset']['id']
    
    file.seek(0)
    upload_response = requests.put(upload_url, data=file)

    print(f"Upload response: {upload_response.status_code}")
    
    if upload_response.status_code == 200:
        print(f"Asset uploaded successfully. Asset ID: {asset_id}")
        time.sleep(30)
        return asset_id
    else:
        print(f"Failed to upload asset. Status code: {upload_response.status_code}")
        return None
    
@app.route('/update_credits', methods=['POST'])
def update_credits():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    credits_to_add = int(request.form.get('credits', 0))
    
    cursor = mysql.connection.cursor()
    cursor.execute("""UPDATE users SET image_generations_remaining = image_generations_remaining + %s WHERE user_id = %s""", (credits_to_add, user_id))
    mysql.connection.commit()
    
    return redirect('/')

def get_profile_photo(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT photo FROM users WHERE user_id = '{}'""".format(user_id))
    photo = cursor.fetchone()

    if photo:
        return photo[0]
    else:
        return None

if __name__ == '__main__':
    app.run()


