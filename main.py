import json
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

        # This queue is used to play previous songs and serves as a history collection
        self.previous_queue = queue.LifoQueue()

        # This array is used to populate song present in a collection, i.e. a playlist or album. When a collection
        # is loaded, this array is populated will all these values, even if not played. Once the song is played, the
        # collection queue is created by omitting details from the potential playlist that have already been played
        self.potential_tracks = []

        self.is_playing = False

    # ____________________________________
    # | This batch of methods are for    |
    # | clearing and populating specific |
    # | elements related to the DOM      |
    # |__________________________________|

    def page_setup(self):
        window.evaluate_js("document.getElementById('seek-obj').style.backgroundColor = '#FFFFFF'")

    def replace_apostrophe(self, string):
        return string.replace("%27", "׳")


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

                new_tag.appendChild(tag_left_component);
                new_tag.appendChild(tag_right_component);

                tag_left_component.appendChild(song_name_element);
                tag_right_component.appendChild(add_to_queue_text);

                document.getElementById('tag-container').appendChild(new_tag);

            """ % (navigation_url, navigation_url, song_name)

        window.evaluate_js(javascript_code)

    def get_current_time(self):
        time = window.evaluate_js("document.getElementById('audio').currentTime")
        return time

    def set_pause_button(self):
        window.evaluate_js("document.getElementById('music-button').src = 'http://localhost:8080/images/PauseButton.png';")

    def set_play_button(self):
        window.evaluate_js("document.getElementById('music-button').src = 'http://localhost:8080/images/PlayButton.png';")

    # ____________________________________
    # | This batch of methods are for    |
    # | fetching and populating different|
    # | artists and albums               |
    # |__________________________________|

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

            image_url = f"http://localhost:8080/Music/Music/{url}artist_image.jpg"

            artist_name = unquote(url)

            # For everyone who comes after me, I apologize so much for this. The character ׳ is not in fact, a
            # single quotation mark. It is instead a specific unicode greek letter. God help us
            artist_name = self.replace_apostrophe(artist_name)

            javascript_code = """
                    allArtistsContainer = document.createElement('div');
                    allArtistsContainer.setAttribute('class','all-artists-container');
                    
                    allArtistsContainer.id = 'all-artists-container';
                        
                    document.getElementById('item-container').appendChild(allArtistsContainer);
                """

            window.evaluate_js(javascript_code)

            if artist_name[0] != ".":
                javascript_code = """
                        
                        allArtistsContainer = document.getElementById('all-artists-container');
                        
                        new_tag = document.createElement('div');
                        new_tag.setAttribute('class', 'artist-tag');
    
                        newContainer = document.createElement('div');
                        newContainer.setAttribute('class', 'artist-container');
    
                        new_tag.addEventListener('click', function(){
                             populate_artist_work('%s');
                        });
    
                        artistPicture = document.createElement('img');
                        artistPicture.src = '%s';
                        artistPicture.setAttribute('class','artist-picture');
    
                        artist_name_element = document.createElement('h2');
                        artist_name_element.innerText = '%s';
    
                        newContainer.appendChild(new_tag);
    
                        new_tag.appendChild(artistPicture)
                        new_tag.appendChild(artist_name_element);
    
                        allArtistsContainer.appendChild(newContainer)
                            
                    """ % (url, image_url, artist_name[:-1])

                window.evaluate_js(javascript_code)

    def populate_album_info(self, cover_url, album_name, artist_name):
        self.clear_potential_tracks()

        javascript_code = """
            document.getElementById('container-info').style.visibility = 'visible';
            document.getElementById('container-info-cover').src = '%s'
            document.getElementById('container-info-text1').innerHTML = '%s';
            document.getElementById('container-info-text2').innerHTML = '%s';
            document.getElementById('item-container').style.marginLeft = '20vw';
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
            if href[-4:] != ".jpg":
                albums.append(href)

        self.clear_content_view()

        window.evaluate_js("document.getElementById('container-info').style.visibility = 'hidden'")
        window.evaluate_js(f"document.getElementById('item-container').style.marginLeft = '2vw'")

        self.clear_content_view()

        for embed_url in albums:

            album_name = unquote(embed_url)

            # For everyone who comes after me, I apologize so much for this. The character ׳ is not in fact, a
            # single quotation mark. It is instead a specific unicode greek letter. God help us
            album_name = self.replace_apostrophe(album_name)

            if album_name[0] != ".":
                navigation_url = f"{url}{embed_url}"

                cover_url = f"http://localhost:8080/Music/Music/{url}{embed_url}cover.jpg"

                javascript_code = """
                    new_tag = document.createElement('div');
                    new_tag.setAttribute('class', 'album-tag');

                    new_tag.addEventListener('click', function(){
                         populate_songs_from_album('%s');
                    });

                    coverSection = document.createElement('div');
                    textSection = document.createElement('div');
                    
                    coverSection.width = '50vw';

                    coverImage = document.createElement('img');
                    coverImage.setAttribute('class','artist-view-album');
                    coverImage.src = '%s';

                    album_qualifier = document.createElement('h3');
                    album_qualifier.innerText = "ALBUM";
                    album_qualifier.width = '100vw';
                    album_qualifier.style.borderBottom = "2px solid #FFFFFF";

                    album_name_element = document.createElement('h1');
                    album_name_element.innerText = '%s';

                    coverSection.appendChild(coverImage);
                    
                    textSection.appendChild(album_qualifier);
                    textSection.appendChild(album_name_element);
                    
                    new_tag.appendChild(coverSection);
                    new_tag.appendChild(textSection);

                    document.getElementById('item-container').appendChild(new_tag);
                """ % (navigation_url, cover_url, album_name[:-1])

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

        # create div holder for song content
        javascript_code = """
            tag_container = document.createElement('div');
            tag_container.setAttribute('class', 'tag-container');
            tag_container.setAttribute('id', 'tag-container');

            document.getElementById('item-container').appendChild(tag_container);
        """
        window.evaluate_js(javascript_code)

        song_num = 0
        # go through all song links present in html
        for embed_url in songs:

            # add contents to potential queue
            self.potential_tracks.append(f"http://localhost:8080/Music/Music/{url}{embed_url}")

            # increment counter to keep track of which track number the song is
            song_num += 1

            # unquote removes html specific characters from the song url
            song_name = unquote(embed_url)
            song_name = self.replace_apostrophe(song_name)


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
        song_name = self.replace_apostrophe(song_name)

        album_url = url.split("/")[-2]
        album_name = unquote(album_url)
        album_name = self.replace_apostrophe(song_name)

        artist_url = url.split("/")[-3]
        artist_name = unquote(artist_url)
        artist_name = self.replace_apostrophe(artist_name)


        total_url = new_url + "/cover.jpg"

        # window.evaluate_js(f"document.getElementById('container-info').style.visibility = 'hidden'")

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

        javascript_code = """
            newTag = document.createElement('div');
            newTag.setAttribute('class', 'song-tag');

            newTag.addEventListener('click', function(){
                create_new_playlist()                     
            });
            
            tagText = document.createElement('h4');
            tagText.innerText = 'NEW PLAYLIST';

            document.getElementById('item-container').appendChild(newTag);

            newTag.appendChild(tagText);
        """
        window.evaluate_js(javascript_code)

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

    # ____________________________________
    # | This batch of methods are for    |
    # | navigating elements and          |
    # | some functionality of buttons    |
    # |__________________________________|
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
            window.evaluate_js(
                "document.getElementById('music-button').src = 'http://localhost:8080/images/PlayButton.png';")
            window.evaluate_js("document.getElementById('audio').pause();")
            self.is_playing = False

        else:
            window.evaluate_js(
                "document.getElementById('music-button').src = 'http://localhost:8080/images/PauseButton.png';")
            window.evaluate_js("document.getElementById('audio').play();")
            self.is_playing = True

    def play_song_from_click(self, url):
        self.collection_queue.queue.clear()

        if self.potential_tracks:
            for i in range(len(self.potential_tracks)):
                url_content = self.potential_tracks[i]
                if url_content == url:
                    for remaining_track in self.potential_tracks[i + 1:]:
                        next_eligible_song = remaining_track
                        self.collection_queue.put(next_eligible_song)
                    break

        self.play_song(url)

    # ____________________________________
    # | This batch of methods are for    |
    # | playing songs and handling       |
    # | autoplay / queue functionality   |
    # |__________________________________|
    def play_song(self, url):
        window.evaluate_js("document.getElementById('audio').currentTime = 0;")

        self.previous_queue.put(url)

        self.populate_player_view(url)

        self.set_pause_button()
        window.evaluate_js(f"document.getElementById('audio').src = '{url}'")
        window.evaluate_js(f"document.getElementById('audio').play()")

    def add_to_queue(self, url):
        self.song_queue.put(url)

    def play_next_song(self):

        if self.song_queue.empty():
            if self.collection_queue.empty():
                window.evaluate_js("document.getElementById('audio').currentTime = 0;")
                self.set_play_button()
            else:
                collection_queue_next = self.collection_queue.get()
                self.play_song(collection_queue_next)

        else:
            self.collection_queue.queue.clear()

            next_song_url = self.song_queue.get()
            self.play_song(next_song_url)
            self.populate_player_view(next_song_url)

    def play_last_song(self):
        current_time = self.get_current_time()

        if not self.previous_queue.empty():
            if self.get_current_time() < 1:
                self.previous_queue.get()
                song = self.previous_queue.get()
                self.play_song(song)
            else:
                window.evaluate_js("document.getElementById('audio').currentTime = 0;")
        else:
            window.evaluate_js("document.getElementById('audio').currentTime = 0;")

    def skip_song(self):
        self.play_next_song()

    # ____________________________________
    # | This batch of methods are for    |
    # | handling adjusting and adding to |
    # | playlists                        |
    # |__________________________________|

    def get_playlists_conflig(self):
        playlist_config_file = open("configuration/playlists.json")
        playlist_json = json.load(playlist_config_file)
        return playlist_json

    def create_new_playlist(self):
        playlist_json = self.get_playlists_conflig()

        playlist_id = len(playlist_json) + 1

        playlist_json[str(playlist_id)] = {"name": "New Playlist", "cover": "", "contents": {}, "enabled":True}

        with open("configuration/playlists.json", "w") as outfile:
            json.dump(playlist_json, outfile)

    def playlist_set_name(self, playlist_id, playlist_name):
        playlist_json = self.get_playlists_conflig()

        playlist_json[playlist_id]["name"] = playlist_name

        with open("configuration/playlists.json", "w") as outfile:
            json.dump(playlist_json, outfile)

    def playlist_set_cover(self, playlist_id, cover_url):
        playlist_json = self.get_playlists_conflig()

        playlist_json[playlist_id]["cover"] = cover_url

        with open("configuration/playlists.json", "w") as outfile:
            json.dump(playlist_json, outfile)

    def playlist_add_song(self, playlist_id, song_url):
        playlist_json = self.get_playlists_conflig()

        num_songs_in_playlist = len(playlist_json[playlist_id]["contents"])

        playlist_json[playlist_id]["contents"][(num_songs_in_playlist+1)] = song_url

        with open("configuration/playlists.json", "w") as outfile:
            json.dump(playlist_json, outfile)

    def playlist_remove_song(self, playlist_id, song_id):
        playlist_json = self.get_playlists_conflig()
        playlist = playlist_json[playlist_id]["contents"]

        playlist.pop(song_id)
        for id in playlist:
            id = int(id)
            if id < int(song_id):
                new_id = id - 1
                playlist[str(id)] = playlist[id]
                del playlist[id]

        with open("configuration/playlists.json", "w") as outfile:
            json.dump(playlist_json, outfile)



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
