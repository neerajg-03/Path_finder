import requests
from pprint import pprint

# List of locations in Delhi (place names only)
locations = [
    {"name": "Hawa Mahal", "category": "monument", "avgTime": 30, "rating": 4.5},
    {"name": "Jantar Mantar", "category": "monument", "avgTime": 60, "rating": 4.7},
    {"name": "RajMandir Cinema", "category": "monument", "avgTime": 90, "rating": 4.6},
    {"name": "Lotus Temple", "category": "monument", "avgTime": 45, "rating": 4.8},
    {"name": "Connaught Place", "category": "shopping", "avgTime": 120, "rating": 4.4},
    {"name": "Hauz Khas Village", "category": "adventurous", "avgTime": 60, "rating": 4.5},
    {"name": "Jama Masjid", "category": "monument", "avgTime": 50, "rating": 4.3},
    {"name": "Lodhi Garden", "category": "park", "avgTime": 60, "rating": 4.6},
    {"name": "Humayun's Tomb", "category": "monument", "avgTime": 75, "rating": 4.7},
    {"name": "Akshardham Temple", "category": "temple", "avgTime": 90, "rating": 4.9},
    {"name": "Albert Hall Museum", "category": "museum", "avgTime": 120, "rating": 4.5},
    {"name": "Garden of Five Senses", "category": "park", "avgTime": 30, "rating": 4.4}
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

    # Print the raw response for debugging
    pprint(geocode_result)

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
        k = 0.1  # Weight for travel time; adjust this value as needed
        score = loc['rating'] / (k * travel_time + 1)  # Higher weight on rating
        loc['travelTime'] = travel_time
        loc['score'] = score  # Store the score in the location dictionary

    # Filter out locations without a valid score before sorting
    valid_locations = [loc for loc in locations if 'score' in loc]

    # Sort locations by score (higher score preferred)
    locations_sorted = sorted(valid_locations, key=lambda loc: loc['score'], reverse=True)

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


# Function to create Google Maps URL for itinerary
def create_google_maps_url(itinerary):
    base_url = "https://www.google.com/maps/dir/?api=1"
    waypoints = []

    # Add each location in the itinerary as a waypoint
    for loc in itinerary:
        waypoints.append(f"{loc['latitude']},{loc['longitude']}")

    # Create the final URL
    waypoints_param = "|".join(waypoints)
    url = f"{base_url}&origin={itinerary[0]['latitude']},{itinerary[0]['longitude']}&destination={itinerary[-1]['latitude']},{itinerary[-1]['longitude']}&waypoints={waypoints_param}&travelmode=driving"
    return url


# Example usage
if __name__ == "__main__":
    # Current location name
    current_location_name = "Nahargarh Fort"  # We'll fetch the coordinates for this using the API
    available_time = 600  # Total available time in minutes (6 hours)

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

    # Create and print the Google Maps URL
    maps_url = create_google_maps_url(itinerary)
    print(f"\nYou can view your itinerary on Google Maps here: {maps_url}")
