from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import csv
from datetime import datetime
from geopy.distance import geodesic

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maindata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(100), nullable=False)
    coordinates = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Location(area={self.area}, coordinates={self.coordinates})>'
    
class WaterAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    water_source = db.Column(db.String(50), nullable=False)
    water_level = db.Column(db.String(50), nullable=False)
    water_quality_ph = db.Column(db.Float, nullable=False)
    water_quality_turbidity = db.Column(db.String(50), nullable=False)
    water_availability_status = db.Column(db.String(50), nullable=False)
    additional_notes = db.Column(db.Text)

    def __repr__(self):
        return f'<WaterAvailability(area={self.area}, date={self.date}, water_source={self.water_source}, water_level={self.water_level}, water_quality_ph={self.water_quality_ph}, water_quality_turbidity={self.water_quality_turbidity}, water_availability_status={self.water_availability_status}, additional_notes={self.additional_notes})>'

def populate_location_data():
    with open('loc.csv', 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            coordinates_str = row['Latitude, Longitude']
            latitude, longitude = map(float, coordinates_str.split(','))

            location = Location(area=row['Area'], coordinates=f"{latitude}, {longitude}")
            db.session.add(location)
        db.session.commit()

def populate_water_availability_data():
    with open('maindata.csv', 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            date_str = row['Date']
            date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()

            water_availability = WaterAvailability(
                area=row['Site/Area Name'],
                date=date_obj,
                water_source=row['Water Source'],
                water_level=row['Water Level (in meters)'],
                water_quality_ph=row['Water Quality (pH)'],
                water_quality_turbidity=row['Water Quality (Turbidity)'],
                water_availability_status=row['Water Availability Status'],
                additional_notes=row['Additional Notes/Comments']
            )
            db.session.add(water_availability)
        db.session.commit()

def get_city_names():
    city_tuples = WaterAvailability.query.with_entities(WaterAvailability.area).all()
    city_names = [city[0] for city in city_tuples]
    return city_names

@app.route('/')
def index():
    city_names = get_city_names()
    return render_template('index.html', city_names=city_names)

@app.route('/', methods=['POST'])
@app.route('/', methods=['POST'])
def search():
    city_names = get_city_names()
    if request.method == 'POST':
        dropdown_value = request.form['dropdown']
        search_text = request.form['search_text']
        if search_text:
            # Check if the search text contains valid coordinates
            try:
                latitude, longitude = map(float, map(str.strip, search_text.split(',')))
                print("Latitude:", latitude)
                print("Longitude:", longitude)
            except ValueError:
                print("Invalid input format. Please enter latitude and longitude separated by comma.")
                return render_template('index.html', city_names=city_names, error_message="Invalid input format. Please enter latitude and longitude separated by comma.")

            # Find the nearest city based on the provided coordinates
            nearest_city_info, error_message, distance = find_nearest_city((latitude, longitude))
            if nearest_city_info:
                return render_template('result.html', city_name=nearest_city_info['city_name'], water_availability_info=nearest_city_info['water_availability_info'], distance = round(distance, 3))
            else:
                print(error_message)
                return render_template('index.html', city_names=city_names, error_message=error_message)
        else:
            # If no search text is provided, show water availability information for the selected city
            water_availability_info = WaterAvailability.query.filter_by(area=dropdown_value).all()
            return render_template('result.html', city_name=dropdown_value, water_availability_info=water_availability_info)
    else:
        return render_template('index.html', city_names=city_names)

def find_nearest_city(coord):
    # Parse the given coordinate
    given_lat, given_lon = float(coord[0]), float(coord[1])

    # Check if latitude is within valid range
    if not (-90 <= given_lat <= 90):
        return None, "Latitude must be in the [-90; 90] range.", None

    # Query all cities and their coordinates from the database
    cities = Location.query.all()

    # Initialize variables for nearest city and distance
    nearest_city = None
    min_distance = float('inf')

    # Loop through each city and calculate distance
    for city in cities:
        city_lat, city_lon = map(float, city.coordinates.split(','))

        # Calculate distance between given coordinate and city's coordinates
        distance = geodesic((given_lat, given_lon), (city_lat, city_lon)).kilometers

        # Check if the city is within 10 km radius and closest so far
        if distance < 10 and distance < min_distance:
            min_distance = distance
            nearest_city = city

    # If nearest city found, query its water availability information
    if nearest_city:
        water_availability_info = WaterAvailability.query.filter_by(area=nearest_city.area).all()
        return {'city_name': nearest_city.area, 'distance': min_distance, 'water_availability_info': water_availability_info}, None, min_distance
    else:
        return None, "No city found within 10 km radius.", None


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Location.query.first() and not WaterAvailability.query.first():
            populate_location_data()
            populate_water_availability_data()

    app.run(debug=True)
