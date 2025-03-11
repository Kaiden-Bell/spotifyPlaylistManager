import requests
from flask import Flask, redirect, request, session, url_for
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Change this to something strong for security

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Must match your Spotify app's redirect URI
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

# Scope defines what data you can access (playlist details in this case)
SCOPE = "playlist-read-private"

@app.route('/')
def home():
    return '''
    <h1>Spotify Playlist Viewer</h1>
    <a href="/login">Login with Spotify</a>
    '''

@app.route('/login')
def login():
    auth_url = f"{SPOTIFY_AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided."

    # Exchange code for an access token
    token_response = requests.post(SPOTIFY_TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })

    token_info = token_response.json()
    session['access_token'] = token_info['access_token']
    
    return redirect(url_for('playlist_viewer'))

@app.route('/playlist', methods=['POST'])
def playlist_viewer():
    playlist_url = request.form['playlist_url']
    playlist_id = playlist_url.split('/')[-1].split('?')[0]  
    access_token = session.get('access_token')
    
    if not access_token:
        return redirect('/login')

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers)
    
    if response.status_code != 200:
        return "Error fetching playlist."

    data = response.json()
    track_data = [{"name": t['track']['name'], "artist": t['track']['artists'][0]['name']} for t in data['items']]

    return f"<h3>Tracks in Playlist:</h3> {track_data}"

if __name__ == '__main__':
    app.run(debug=True)
