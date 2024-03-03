from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import csv
from datetime import datetime

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
            # Split the coordinates string into latitude and longitude
            coordinates_str = row['Latitude, Longitude']
            latitude, longitude = map(float, coordinates_str.split(','))

            location = Location(area=row['Area'], coordinates=f"{latitude}, {longitude}")
            db.session.add(location)
        db.session.commit()

def populate_water_availability_data():
    with open('maindata.csv', 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convert date string to Python date object
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

# Define routes
@app.route('/')
def index():
    city_names = get_city_names()  # Fetch city names here
    return render_template('index.html', city_names=city_names)

@app.route('/', methods=['GET', 'POST'])
def search():
    city_names = get_city_names()  # Fetch city names here
    if request.method == 'POST':
        dropdown_value = request.form['dropdown']
        search_text = request.form['search_text']
        water_availability_info = WaterAvailability.query.filter_by(area=dropdown_value).all()
        return render_template('result.html', city_name=dropdown_value, water_availability_info=water_availability_info)
    else:
        return render_template('index.html', city_names=city_names)

        # Perform search or any other action here
        # print(f"Dropdown Value: {dropdown_value}, Search Text: {search_text}")
    # return render_template('index.html', city_names=city_names)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Check if Location and WaterAvailability tables have records
        if not Location.query.first() and not WaterAvailability.query.first():
            populate_location_data()  # Populate location data
            populate_water_availability_data()  # Populate water availability data

    app.run(debug=True)
