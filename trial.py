
import spotipy
import spotipy.oauth2

CLIENT_SIDE_URL = "http://spotifyanalysis.us-west-2.elasticbeanstalk.com"
PORT = 8080
REDIRECT_URI = "{}/playlists".format(CLIENT_SIDE_URL)
SCOPE = ("playlist-modify-public playlist-modify-private "
         "playlist-read-collaborative playlist-read-private")



# the next three functions are meant to help with getting the spotify information
def get_oauth():
    """Return a Spotipy Oauth2 object."""
    prefs = get_prefs()
    return spotipy.oauth2.SpotifyOAuth(
        prefs["ClientID"], prefs["ClientSecret"], REDIRECT_URI, scope=SCOPE,
        cache_path=".tokens")


def get_spotify(auth_token=None):
    """Return an authenticated Spotify object."""
    oauth = get_oauth()
    token_info = oauth.get_cached_token()
    if not token_info and auth_token:
        token_info = oauth.get_access_token(auth_token)
    return spotipy.Spotify(token_info["access_token"])


def get_prefs():
    """Get application prefs plist and set secret key.
    Args:
        path: String path to a plist file.
    """
    prefs = {'ClientID' : 'f48bed994e9a4ab9a939688387022cb2',
             'ClientSecret': '4a31ad0a2e5540e6a8b0486cc2915ffe'}
    return prefs


print(get_oauth().get_authorize_url())