import threading
import webview
import http.server
import socketserver
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import queue

class Api:
    def __init__(self):
        self.cancel_heavy_stuff_flag = False
        self.current_working_url = ""

        # this navigation queue is used to log movement within the view, it corresponds to the methods
        # loading pages
        self.navigation_queue = queue.LifoQueue()

        # This queue corresponds to songs explicitly added to a queue, it serves as the priority over all
        # other song playing queues
        self.song_queue = queue.Queue()

        # This queue is used to play the next song present in albums and playlists, if there is nothing in the queue
        # it handles autoplay from the album
        self.collection_queue = queue.Queue()

        # This array is used to populate song present in a collection, i.e. a playlist or album. When a collection
        # is loaded, this array is populated will all these values, even if not played. Once the song is played, the
        # collection queue is created by omitting details from the potential playlist that have already been played
        self.potential_tracks = []


        self.is_playing = False

    def clear_content_view(self):
        window.evaluate_js("document.getElementById('item-container').innerHTML = ''")

    def clear_potential_tracks(self):
        self.potential_tracks = []

    def populate_song_tag(self, navigation_url, song_name):
        javascript_code = """
                new_tag = document.createElement('div');
                new_tag.setAttribute('class', 'song-tag');
                new_tag.style.justifyContent = 'space-between';

                tag_left_component = document.createElement('div');
                tag_left_component.setAttribute('class','song-tag-left');
                tag_left_component.style.width = '80vw';

                tag_right_component = document.createElement('div');
                tag_right_component.setAttribute('class','song-tag-right');
                
                tag_left_component.addEventListener('click', function(){
                    play_song_from_click('%s');
                });

                tag_right_component.addEventListener('click', function(){
                    add_to_queue('%s');
                });

                song_name_element = document.createElement('h4');
                song_name_element.innerText = '%s';

                add_to_queue_text = document.createElement('h4');
                add_to_queue_text.innerText = '+';

                document.getElementById('item-container').appendChild(new_tag);

                new_tag.appendChild(tag_left_component);
                new_tag.appendChild(tag_right_component);

                tag_left_component.appendChild(song_name_element);
                tag_right_component.appendChild(add_to_queue_text);

            """ % (navigation_url, navigation_url,  song_name)

        window.evaluate_js(javascript_code)


    def get_artists(self):
        reqs = requests.get('http://localhost:8080/Music/Music')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        self.navigation_queue.put(("get_artists", ""))

        self.clear_potential_tracks()
        self.clear_content_view()

        urls = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href[0] != ".":
                urls.append(href)

        for url in urls:

            artist_name = unquote(url)

            if artist_name[0] != ".":
                javascript_code = """
                        new_tag = document.createElement('div');
                        new_tag.setAttribute('class', 'song-tag');
    
                        new_tag.addEventListener('click', function(){
                             populate_artist_work('%s');
                        });
    
                        artist_name_element = document.createElement('h4');
                        artist_name_element.innerText = '%s';
    
                        new_tag.appendChild(artist_name_element);
    
                        document.getElementById('item-container').appendChild(new_tag);
    
                    """ % (url, artist_name[:-1])

                window.evaluate_js(javascript_code)


    def populate_album_info(self, cover_url, album_name, artist_name):
        self.clear_potential_tracks()

        javascript_code = """
            document.getElementById('container-info').style.visibility = 'visible';
            document.getElementById('container-info-cover').src = '%s'
            document.getElementById('container-info-text1').innerHTML = '%s';
            document.getElementById('container-info-text2').innerHTML = '%s';
            document.getElementById('item-container').style.marginLeft = '33vw';
        """ % (cover_url, album_name, artist_name)

        window.evaluate_js(javascript_code)


    def populate_artist_work(self, url):

        reqs = requests.get(f'http://localhost:8080/Music/Music/{url}')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        self.current_working_url = f"http://localhost:8080/Music/Music/{url}"

        self.navigation_queue.put(("populate_artist_work", url))
        self.clear_potential_tracks()


        albums = []
        for link in soup.find_all('a'):
            href = link.get('href')
            albums.append(href)

        self.clear_content_view()

        window.evaluate_js("document.getElementById('container-info').style.visibility = 'hidden'")
        window.evaluate_js(f"document.getElementById('item-container').style.marginLeft = '2vw'")

        self.clear_content_view()

        for embed_url in albums:

            album_name = unquote(embed_url)

            if album_name[0] != ".":

                navigation_url = f"{url}{embed_url}"

                javascript_code = """
                    new_tag = document.createElement('div');
                    new_tag.setAttribute('class', 'song-tag');

                    new_tag.addEventListener('click', function(){
                         populate_songs_from_album('%s');
                    });

                    album_name_element = document.createElement('h4');
                    album_name_element.innerText = '%s';

                    document.getElementById('item-container').appendChild(new_tag);

                    new_tag.appendChild(album_name_element);
                """ % (navigation_url, album_name[:-1])

                window.evaluate_js(javascript_code)

    def populate_songs_from_album(self, url):

        # clear existing potential queue to represent new content loaded
        self.clear_potential_tracks()

        # fetch song links from locally hosted server
        reqs = requests.get(f'http://localhost:8080/Music/Music/{url}')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        # append current method into navigation queue
        self.current_working_url = f"http://localhost:8080/Music/Music/{url}"
        self.navigation_queue.put(("populate_songs_from_album", url))

        # get cover url to display album artwork for view
        cover_url = f"http://localhost:8080/Music/Music/{url}/cover.jpg"

        # Because the song url is structured as "Artist/Album/Song" we can split the navigation string
        # and index for this information

        album_url = url.split("/")[-2]
        album_name = unquote(album_url)

        artist_url = url.split("/")[-3]
        artist_name = unquote(artist_url)

        # filtering all songs links from server
        songs = []
        for link in soup.find_all('a'):
            href = link.get('href')
            songs.append(href)

        # clear div content for new view
        self.clear_content_view()

        # this method just populates the dom view to display album cover and artist names
        self.populate_album_info(cover_url, album_name, artist_name)


        song_num = 0
        # go through all song links present in html
        for embed_url in songs:

            # add contents to potential queue
            self.potential_tracks.append(f"http://localhost:8080/Music/Music/{url}{embed_url}")

            # increment counter to keep track of which track number the song is
            song_num += 1

            # unquote removes html specific characters from the song url
            song_name = unquote(embed_url)

            # filtering out "." files, removing unwanted directories
            if song_name[0] != ".":

                if song_name[-4:] == ".mp3":

                    # keep track of full url to append to audio element in the dom

                    navigation_url = f"http://localhost:8080/Music/Music/{url}{embed_url}"
           
                    song_name = song_name[:-4]
                    song_name = " ".join(song_name.split(" ")[1:])

                    self.populate_song_tag(navigation_url, song_name)


    def populate_player_view(self, url):

        self.is_playing = True

        new_url = "/".join(url.split("/")[:-1])
         
        mp3_url = url.split("/")[-1]
        song_name = (unquote(mp3_url))[:-4]
        song_name = " ".join(song_name.split(" ")[1:])
        

        album_url = url.split("/")[-2]
        album_name = unquote(album_url)
        
        artist_url = url.split("/")[-3]
        artist_name = unquote(artist_url)

        total_url = new_url+"/cover.jpg"
       
        #window.evaluate_js(f"document.getElementById('container-info').style.visibility = 'hidden'")
 
        window.evaluate_js(f"document.getElementById('song-display-cover').src = '{total_url}'")

        window.evaluate_js(f"document.getElementById('song-display-song-name').innerHTML = '{song_name}'")
        window.evaluate_js(f"document.getElementById('song-display-artist-name').innerHTML = '{artist_name}'")

        window.evaluate_js(f"document.getElementById('player-bar-cover').src = '{total_url}'")
        window.evaluate_js(f"document.getElementById('player-bar-title').innerHTML = '{song_name}'")
        window.evaluate_js(f"document.getElementById('player-bar-artist').innerHTML = '{artist_name}'")

    def populate_available_playlists(self):
        reqs = requests.get(f'http://localhost:8080/configuration/playlists.json')
        self.navigation_queue.put(("populate_available_playlists", ""))

        playlist_info = reqs.json()

        self.clear_potential_tracks()
        self.clear_content_view()

        # get all playlists
        for playlist_id in playlist_info:
            playlist_name = playlist_info[playlist_id]['name']

            javascript_code = """
                new_tag = document.createElement('div');
                new_tag.setAttribute('class', 'song-tag');

                new_tag.addEventListener('click', function(){
                    populate_playlist(%s)                     
                });

                album_name_element = document.createElement('h4');
                album_name_element.innerText = '%s';

                document.getElementById('item-container').appendChild(new_tag);

                new_tag.appendChild(album_name_element);
            """ % (playlist_info[playlist_id], playlist_name)

            window.evaluate_js(javascript_code)

    def populate_playlist(self, playlist_content_json):
        self.navigation_queue.put(("populate_songs_from_album", playlist_content_json))

        # clear potential queue to represent new content being loaded
        self.clear_potential_tracks()

        self.clear_content_view()

        cover_url = f"{playlist_content_json['cover']}"

        song_content = playlist_content_json['contents']

        for song in song_content:
            parsed_song_url = song_content[song]

            self.potential_tracks.append(parsed_song_url)

            song_url = parsed_song_url.split("/")[-1][:-4]
            song_name = unquote(song_url)

            album_url = parsed_song_url.split("/")[-2]
            album_name = unquote(album_url)

            artist_url = parsed_song_url.split("/")[-3]
            artist_name = unquote(artist_url) 

            self.populate_song_tag(parsed_song_url, song_name)


    def navigate_back(self):

        # pop off the last two elements of the queue to get the last performed action
        last_action = self.navigation_queue.get()
        last_action = self.navigation_queue.get()

        # navigation queue is stored as a tuple, get just the method
        last_action_method = last_action[0]

        # get the corresponding url to populate the proper information from view
        url = last_action[1]        

        if last_action_method == "populate_songs_from_album":
            self.populate_songs_from_album(url)

        elif last_action_method == "populate_artist_work":
            self.populate_artist_work(url)

        elif last_action_method == "populate_available_playlists":
            self.populate_available_playlists()

        elif last_action_method == "populate_playlist":
            self.populate_playlist(url)

        elif last_action_method == "get_artists":
            self.get_artists()
        
 
    def toggle_music(self):

        if self.is_playing:
            window.evaluate_js("document.getElementById('music-button').src = 'http://localhost:8080/images/PlayButton.png';")
            window.evaluate_js("document.getElementById('audio').pause();")
            self.is_playing = False

        else:
            window.evaluate_js("document.getElementById('music-button').src = 'http://localhost:8080/images/PauseButton.png';")
            window.evaluate_js("document.getElementById('audio').play();")
            self.is_playing = True

    def play_song_from_click(self, url):
        self.collection_queue.queue.clear()

        if self.potential_tracks:
            for i in range(len(self.potential_tracks)):
                url_content = self.potential_tracks[i]
                if url_content == url:
                    for remaining_track in self.potential_tracks[i+1:]:

                        next_eligible_song = remaining_track
                        print(f"PUTTING {next_eligible_song} in the collection queue")
                        self.collection_queue.put(next_eligible_song)
                    break

        self.play_song(url)

    def play_song(self, url):
        window.evaluate_js("document.getElementById('audio').currentTime = 0;'")

        self.populate_player_view(url)

        window.evaluate_js("document.getElementById('music-button').src = "
                           "'http://localhost:8080/images/PauseButton.png';")
        window.evaluate_js(f"document.getElementById('audio').src = '{url}'")
        window.evaluate_js(f"document.getElementById('audio').play()")

    def add_to_queue(self, url):
        self.song_queue.put(url)

    def play_next_song(self):

        if self.song_queue.empty():
            if self.collection_queue.empty():
                window.evaluate_js("document.getElementById('audio).currentTime = 0;")
                window.evaluate_js(f"document.getElementById('music-button').src = 'http://localhost:8080/images/PlayButton.png';")
            else:
                collection_queue_next = self.collection_queue.get()
                self.play_song(collection_queue_next)

        else:
            self.collection_queue.queue.clear()

            next_song_url = self.song_queue.get()
            self.play_song(next_song_url)
            self.populate_player_view(next_song_url)

    def skip_song(self):
        self.play_next_song()

def start_server():
    port = 8080
    directory = "."
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    httpd.serve_forever()

if __name__ == '__main__':

    web_server_thread = threading.Thread(target=start_server)
    web_server_thread.start()

    api = Api()
    window = webview.create_window('Comfy Couches', 'view/index.html', js_api=api, width=1500, height=1000)
    webview.start(debug=True)





