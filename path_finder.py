import requests
from pprint import pprint

# List of locations with their names and other attributes (no coordinates yet)
locations = [
    {"name": "Central Park", "category": "monument", "avgTime": 60, "rating": 4.8},
    {"name": "Statue of Liberty", "category": "monument", "avgTime": 90, "rating": 4.9},
    {"name": "Times Square", "category": "monument", "avgTime": 45, "rating": 4.7},
    {"name": "Empire State Building", "category": "monument", "avgTime": 60, "rating": 4.8},
    {"name": "Brooklyn Bridge", "category": "monument", "avgTime": 60, "rating": 4.6},
    {"name": "MoMA", "category": "museum", "avgTime": 90, "rating": 4.7},
    {"name": "Rockefeller Center", "category": "landmark", "avgTime": 60, "rating": 4.6},
    {"name": "5th Avenue", "category": "shopping", "avgTime": 90, "rating": 4.5},
    {"name": "Madison Square Garden", "category": "sports", "avgTime": 120, "rating": 4.4},
    {"name": "American Museum of Natural History", "category": "museum", "avgTime": 120, "rating": 4.9},
    {"name": "The Met", "category": "museum", "avgTime": 120, "rating": 4.8},
    {"name": "One World Trade Center", "category": "monument", "avgTime": 90, "rating": 4.8}
]

# Your Google Maps API Key (replace with your actual key)
GOOGLE_MAPS_API_KEY = 'AIzaSyAehQ9_Y4o264ULh6XZaid73OEVZVT2_wo'


# Function to get coordinates using Google Maps Geocoding API
def get_coordinates(place_name):
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": place_name,
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(geocode_url, params=params)
    geocode_result = response.json()

    try:
        location = geocode_result['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    except (IndexError, KeyError):
        print(f"Error fetching coordinates for {place_name}")
        return None, None


# Function to calculate travel time using Google Maps Distance Matrix API
def get_travel_time(origin, destination):
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    params = {
        'origins': f"{origin['latitude']},{origin['longitude']}",
        'destinations': f"{destination['latitude']},{destination['longitude']}",
        'key': GOOGLE_MAPS_API_KEY,
        'mode': 'driving'  # You can change to 'walking', 'bicycling', etc.
    }

    response = requests.get(url, params=params)
    result = response.json()

    try:
        travel_time = result['rows'][0]['elements'][0]['duration']['value'] / 60  # Time in minutes
        return travel_time
    except (IndexError, KeyError):
        print(f"Error fetching travel time between {origin['name']} and {destination['name']}")
        return None


# Function to generate an itinerary based on available time
def generate_itinerary(current_location_name, available_time):
    itinerary = []
    suggestions = []
    total_time = 0

    # Get coordinates for the current location
    current_lat, current_lng = get_coordinates(current_location_name)
    if current_lat is None or current_lng is None:
        print(f"Unable to determine coordinates for the current location: {current_location_name}")
        return itinerary, suggestions

    current_location = {"name": current_location_name, "latitude": current_lat, "longitude": current_lng}

    # Calculate travel times and scores for each location
    for loc in locations:
        # Get the coordinates for the destination location
        lat, lng = get_coordinates(loc['name'])
        if lat is None or lng is None:
            continue

        loc["latitude"], loc["longitude"] = lat, lng

        # Fetch the travel time
        travel_time = get_travel_time(current_location, loc)
        if travel_time is None:
            continue

        # Calculate a score based on rating and travel time
        score = loc['rating'] / (travel_time + 1)  # Add 1 to avoid division by zero
        loc['travelTime'] = travel_time
        loc['score'] = score  # Store the score in the location dictionary

    # Sort locations by score (higher score preferred)
    locations_sorted = sorted(locations, key=lambda loc: loc['score'], reverse=True)

    for loc in locations_sorted:
        travel_time = loc['travelTime']
        time_spent = loc['avgTime']
        if total_time + travel_time + time_spent <= available_time:
            itinerary.append(loc)
            total_time += travel_time + time_spent

    # Create suggestions for remaining locations not included in the itinerary
    selected_names = {loc['name'] for loc in itinerary}
    for loc in locations_sorted:
        if loc['name'] not in selected_names:
            travel_time = get_travel_time(current_location, loc)
            if travel_time:
                suggestions.append({**loc, 'proximityScore': travel_time})

    # Sort suggestions by proximity (lower travel time first)
    suggestions_sorted = sorted(suggestions, key=lambda loc: loc['proximityScore'])

    # Limit suggestions to top 5
    return itinerary, suggestions_sorted[:5]


# Example usage
if __name__ == "__main__":
    # Current location name
    current_location_name = "Times Square"  # We'll fetch the coordinates for this using the API
    available_time = 180  # Total available time in minutes (6 hours)

    itinerary, suggestions = generate_itinerary(current_location_name, available_time)

    # Print the itinerary
    print("Itinerary:")
    for index, loc in enumerate(itinerary, start=1):
        print(
            f"{index}. {loc['name']} (Category: {loc['category']}, Rating: {loc['rating']}, Travel Time: {loc['travelTime']} mins, Time Spent: {loc['avgTime']} mins)")

    # Print suggestions for nearby places
    print("\nSuggestions for nearby places you may visit:")
    for index, loc in enumerate(suggestions, start=1):
        print(
            f"{index}. {loc['name']} (Category: {loc['category']}, Rating: {loc['rating']}, Proximity Time: {loc['proximityScore']} mins)")
