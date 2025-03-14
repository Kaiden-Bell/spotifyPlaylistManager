import requests
import os
from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for, request

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key")  # Secure this properly

# Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
SCOPE = "playlist-read-private"

# Home (Landing Page)
@app.route('/')
def home():
    return render_template("index.html")

# Login Route
@app.route('/login')
def login():
    auth_url = f"{SPOTIFY_AUTH_URL}?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={SPOTIFY_REDIRECT_URI}&scope={SCOPE}"
    return redirect(auth_url)

# Spotify Callback (Handles Token Exchange)
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: No authorization code received."

    # Exchange code for access token
    token_response = requests.post(SPOTIFY_TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    })

    token_info = token_response.json()
    session['access_token'] = token_info.get('access_token')

    return redirect(url_for('user_playlists'))  # Redirect to playlists page after login

# Fetch User's Playlists
@app.route('/playlists')
def user_playlists():
    access_token = session.get('access_token')
    
    if not access_token:
        return redirect('/login')

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/me/playlists", headers=headers)
    
    if response.status_code != 200:
        return "Error fetching playlists"

    playlists = response.json().get("items", [])

    user_playlists = []
    for playlist in playlists:
        playlist_id = playlist["id"]
        name = playlist["name"]
        total_tracks = playlist["tracks"]["total"]

        # Fetch total duration of all songs
        track_response = requests.get(f"{SPOTIFY_API_BASE_URL}/playlists/{playlist_id}/tracks", headers=headers)
        track_data = track_response.json()

        # Check if "items" key exists
        if "items" not in track_data:
            continue

        total_duration = sum(
            track["track"]["duration_ms"] for track in track_data["items"]
            if track.get("track") and track["track"].get("duration_ms")  # Check if track exists
        )

        total_minutes = round(total_duration / (1000 * 60), 2)  # Convert to minutes

        user_playlists.append({
            "name": name,
            "total_tracks": total_tracks,
            "total_duration": total_minutes,
            "spotify_url": playlist["external_urls"]["spotify"]
        })

    return render_template("playlists.html", playlists=user_playlists)


# Logout Route (Clears session and redirects to home)
@app.route('/logout')
def logout():
    session.pop('access_token', None)
    return redirect(url_for('home'))

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
