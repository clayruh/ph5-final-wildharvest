#!/usr/bin/env python3
# Remote library imports
from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
import requests
import base64

# Local imports
from config import app, db
from models import User, Plant, Pin
import os

PLANT_ID_API_KEY=os.environ.get('PLANT_ID_API_KEY')
print(PLANT_ID_API_KEY)

app.secret_key = b'u\xd2\xdc\xe82\xa3\xc0\xca\xe7H\xd03oi\xd1\x95\xcc\x7f'

bcrypt = Bcrypt(app)

URL = '/api/v1'

# HELPER METHODS #
def current_user():
    return User.query.filter(User.id == session.get('user_id')).first()

def check_admin():
    return current_user() and current_user().admin

# ============ USER SIGNUP ============ #

@app.post(URL + '/users')
def create_user():
    try:
        data = request.json

        pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        new_user = User(username=data['username'], password_hash=pw_hash, fname=data['fname'], lname=data['lname'], address=data['address'])
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id

        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 406
    
# ============ SESSION LOGIN/LOGOUT ============ #

@app.post(URL + '/login')
def login():
    data = request.json
    print(data)
    user = User.query.filter(User.username == data['username']).first()

    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        session['user_id'] = user.id
        return jsonify(user.to_dict()), 202
    else:
        return jsonify({"message": "Invalid username or password"}), 401
    
@app.get(URL + '/check_session')
def check_session():
    user = current_user()
    if user:
        return jsonify( user.to_dict() ), 200
    else: 
        return {}, 401
    
@app.delete(URL + '/logout')
def logout():
    session['user_id'] = None
    # session.pop('user_id')
    return {}, 204

# ============ USERS ============ #

@app.get('/users')
def get_users():
    users=User.query.all()
    return jsonify([user.to_dict(rules=('-pins.plant_id', '-pins.user_id')) for user in users]), 200

@app.get('/users/<int:id>')
def get_users_by_id(id):
    user=User.query.filter(User.id==id).first()
    return jsonify(user.to_dict(rules=('-pins',))), 200


@app.patch('/users/<int:id>')
def edit_user(id):
    data = request.json
    User.query.filter(User.id == id).update(data)
    db.session.commit()
    user = User.query.filter(User.id == id).first()
    return jsonify(user.to_dict()), 202

@app.delete('/users/<int:id>')
def delete_user(id):
    user = User.query.filter(User.id == id).first()
    db.session.delete(user)
    return jsonify({}), 204

# ============ PINS ============ #

@app.get('/pins')
def get_pins():
    pins = Pin.query.all()
    return jsonify([pin.to_dict(rules=('-user_id',)) for pin in pins]), 200

@app.get('/pins/<int:id>')
def get_pins_by_id(id):
    pin = Pin.query.filter(Pin.id == id).first()
    return jsonify(pin.to_dict(rules=('-user_id',))), 200

@app.post('/pins')
def create_pin():
    data = request.json
    new_pin = Pin(image=data['image'], location=data['location'], comment=data['comment'])
    # somehow will need to grab the current user id that is logged in as well as the plant 
    db.session.add(new_pin)
    db.session.commit()
    return jsonify(new_pin.to_dict()), 201

@app.patch('/pins/<int:id>')
def edit_pin(id):
    data = request.json
    Pin.query.filter(Pin.id == id).update(data)
    db.session.commit()
    pin = Pin.query.filter(Pin.id == id).first()
    return jsonify(pin.to_dict()), 202

@app.delete('/pins/<int:id>')
def delete_pin(id):
    pass

# ============= PLANT ID API ============== #

@app.post(URL + '/process-image')
def process_image():
    # try:
    print(f'WE MADE ITTTTTT: {request.files}')
    # request is empty rn
    # image = request.files['image']
    with open("IMG_5014.jpg", "rb") as file:
        images = [base64.b64encode(file.read()).decode("ascii")]

    if images is not None:
        print("\nwe're gonna get the result?\n")
        result = send_to_plant_id(images)
        print("\nwe got the result\n")
        # print(result["suggestions"][0])
        print("\n\n\n")
        for suggestion in result["suggestions"]:
            print(f" >> {suggestion['plant_name']} -- {suggestion['probability']}%")
            # print(suggestion["plant_name"])
            # print(suggestion["probability"])
    return {"images": images,
            "suggestions": result["suggestions"]}, 200

    # if image and allowed_file(image.filename):
    #     result = send_to_plant_id(image)
    #     return jsonify(result)


        # else:
        #     return jsonify({"error": "Invalid or unsupported image format"})
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}


def send_to_plant_id(images):
    # response = requests.post('https://plant.id/api/v3/identification', files={'image': image})
    response = requests.post(
        "https://api.plant.id/v2/identify",
        json={
            "images": images,
            # "modifiers": ["similar_images"],
            "plant_details": ["common_names", "url"]
        },
        headers={
            "Content-Type": "application/json",
            "Api-Key": "ABVydjecE9RcYXn35O3fp6RRLBXmEi0Cmkd0Fup3Ia5F9dcFMT"
        }
    )
    result = response.json()
    return result

# ============ PLANTS ============ #
@app.get('/plants')
def get_plants():
    plants = Plant.query.all()
    return jsonify([plant.to_dict(rules=('-pins.user_id', '-pins.user.password', '-pins.user.username', '-pins.user.address')) for plant in plants]), 200

@app.get('/plants/<int:id>')
def get_plants_by_id(id):
    plant = Plant.query.filter(Plant.id == id).first()
    return jsonify(plant.to_dict(rules=('-pins.user_id', '-pins.user.password', '-pins.user.username', '-pins.user.address'))), 200

@app.patch('/plants/<int:id>')
def edit_plant(id):
    pass

@app.delete('/plants/<int:id>')
def delete_plant(id):
    pass

# ====================== GOOGLE MAPS API ====================== #
@app.get(URL + '/api/maps/config')
def get_maps_config():
    return jsonify({'apiKey': googlemaps_api_key})

if __name__ == '__main__':
    app.run(port=5555, debug=True)

