from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt
import datetime
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

did_create_tables = False

@app.before_request
def create_tables():
    global did_create_tables
    if not did_create_tables:
        db.create_all()
        did_create_tables = True

from flask import request
from googlemaps import Client
import amadeus

# Initialize the Google Maps client
gmaps = Client(key='AIzaSyB2zGf_NW-AiTMwftjNTH7-vIlSK9cOqOQ')
amadeus_api_key = 'uGhcGgcmVHNiAFP1qSbrGGOfH7ISWhHQ'
amadeus_client_secret = 'IAw7KFZFrHGqJBfG'
amadeus_client = amadeus.Client(client_id=amadeus_api_key, client_secret=amadeus_client_secret)


@app.route('/find_place', methods=['POST'])
def find_place_attractions():
    data = request.get_json()
    place_name = data.get('place_name')

    if not place_name:
        return jsonify({'message': 'No place name provided'}), 400

    # Perform a text search to get the place ID
    search_result = gmaps.places(query=place_name)

    # Check if any places were found
    if not search_result['results']:
        return jsonify({'message': 'No places found'}), 404

    # Get the place ID of the first result
    place_id = search_result['results'][0]['place_id']

    # Get the details of the place
    place_result = gmaps.place(place_id=place_id, fields=['name', 'geometry/location'])

    # Extract location data
    location = place_result["result"]['geometry']['location']
    latitude = location['lat']
    longitude = location['lng']

    # Make a call to get attractions based on location
    attractions_result = gmaps.places_nearby(location=(latitude, longitude), radius=5000, type='tourist_attraction')

    # Check if any attractions were found
    if not attractions_result['results']:
        return jsonify({'message': 'No attractions found in the location'}), 404

    # Return the details of the place and attractions
    response_data = {
        'place_details': place_result,
        'attractions': attractions_result['results']
    }

    return jsonify(response_data)


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query')

    # Get location details
    location_result = gmaps.places(query=query)
    location = location_result['results'][0]['geometry']['location']
    # Get weather data
    weather_response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?lat={location["lat"]}&lon={location["lng"]}&appid=69c90f6d37b478b66354298a4cad125f')
    weather_data = weather_response.json()

    # Get hotel prices (this is a placeholder, replace with actual API call)
    # try:
    #     hotel_search_response = amadeus_client.reference_data.locations.hotels.by_geocode.get(latitude=location['lat'], longitude=location['lng'])


    #     hotel_offers = hotel_search_response.data[0]['hotelId']

    #     hotel_offers = amadeus_client.shopping.hotel_offers_search.get(hotelIds=hotel_offers).data['offers'][0]['id']

    #     hotel_price = amadeus_client.shopping.hotel_offer_search(offer_id=hotel_offers).data[0]['offers'][0]['price']['total']

    # except amadeus.ResponseError as e:
    #     return jsonify({'message': f'Error from Amadeus API: {e}'}), 500
    hotel_offers = []

    # Get popular attractions
    attractions_result = gmaps.places_nearby(location=location, radius=5000, type='tourist_attraction')
    attractions = attractions_result['results']

    return jsonify({
        'location': location,
        'weather': weather_data,
        'hotel_prices': hotel_offers,
        'attractions': attractions
    })

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(username=data['username'], password=hashed_password)
    db.session.add(user)
    db.session.commit()

    token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                       app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'message': 'User created successfully', 'token': token})

@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if user and bcrypt.check_password_hash(user.password, data['password']):
        token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                          app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
