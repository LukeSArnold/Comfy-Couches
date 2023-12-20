import sys
import threading
import time
import webview
import os
import http.server
import socketserver
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, urlunparse, urljoin
import html
import queue

class Api:
    def __init__(self):
        self.cancel_heavy_stuff_flag = False
        self.current_working_url = ""

        self.navigation_queue = queue.LifoQueue()
        self.song_queue = queue.Queue()

        self.is_playing = False

    def get_artists(self):
        reqs = requests.get('http://localhost:8080/Music/Music')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        self.navigation_queue.put(("get_artists", ""))

        window.evaluate_js("document.getElementById('item-container').innerHTML = ''")

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
        

    def populate_artist_work(self, url):

        reqs = requests.get(f'http://localhost:8080/Music/Music/{url}')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        self.current_working_url = f"http://localhost:8080/Music/Music/{url}"

        self.navigation_queue.put(("populate_artist_work", url))


        albums = []
        for link in soup.find_all('a'):
            href = link.get('href')
            albums.append(href)

        #clear div content
        
        window.evaluate_js("document.getElementById('container-info').style.visibility = 'hidden'")
        window.evaluate_js(f"document.getElementById('item-container').style.marginLeft = '2vw'")

        window.evaluate_js("document.getElementById('item-container').innerHTML = ''")

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
        reqs = requests.get(f'http://localhost:8080/Music/Music/{url}')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        self.current_working_url = f"http://localhost:8080/Music/Music/{url}"

        self.navigation_queue.put(("populate_songs_from_album", url))

        cover_url = f"http://localhost:8080/Music/Music/{url}/cover.jpg"

        album_url = url.split("/")[-2]
        album_name = unquote(album_url)

        artist_url = url.split("/")[-3]
        artist_name = unquote(artist_url)

        songs = []
        for link in soup.find_all('a'):
            href = link.get('href')
            songs.append(href)

        #clear div content
        window.evaluate_js("document.getElementById('item-container').innerHTML = ''")

        window.evaluate_js(f"document.getElementById('container-info').style.visibility = 'visible'")
        window.evaluate_js(f"document.getElementById('container-info-cover').src = '{cover_url}'")

        window.evaluate_js(f"document.getElementById('container-info-text1').innerHTML = '{album_name}'")
        window.evaluate_js(f"document.getElementById('container-info-text2').innerHTML = '{artist_name}'")

        window.evaluate_js(f"document.getElementById('item-container').style.marginLeft = '33vw'")

        song_num = 0
        for embed_url in songs:
            song_num += 1

            song_name = unquote(embed_url)

            if song_name[0] != ".":
      
                if song_name[-4:] == ".mp3":

                    navigation_url = f"http://localhost:8080/Music/Music/{url}{embed_url}"
           
                    song_name = song_name[:-4]
                    song_name = " ".join(song_name.split(" ")[1:])

                    #song_name.split(" ")
                    #song_name = " ".join(song_name[1:])
 
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
                            play_song('%s');
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
       
        window.evaluate_js(f"document.getElementById('container-info').style.visibility = hidden")
 
        window.evaluate_js(f"document.getElementById('song-display-cover').src = '{total_url}'")

        window.evaluate_js(f"document.getElementById('song-display-song-name').innerHTML = '{song_name}'")
        window.evaluate_js(f"document.getElementById('song-display-artist-name').innerHTML = '{artist_name}'")

        window.evaluate_js(f"document.getElementById('player-bar-cover').src = '{total_url}'")
        window.evaluate_js(f"document.getElementById('player-bar-title').innerHTML = '{song_name}'")
        window.evaluate_js(f"document.getElementById('player-bar-artist').innerHTML = '{artist_name}'")

        

    def navigate_back(self):
        last_action = self.navigation_queue.get()
        last_action = self.navigation_queue.get()

        
        last_action_method = last_action[0]
        url = last_action[1]        

        if last_action_method == "populate_songs_from_album":
            self.populate_songs_from_album(url)

        elif last_action_method == "populate_artist_work":
            self.populate_artist_work(url)

        elif last_action_method == "get_artists":
            self.get_artists()
        
 
    def toggle_music(self):

        if self.is_playing:
            window.evaluate_js("document.getElementById('music-button').src = 'http://localhost:8080/images/PlayButton.png';")
            window.evaluate_js("document.getElementById('audio').pause();")
            self.is_playing = False
            print("pausing :)")

        else:
            window.evaluate_js("document.getElementById('music-button').src = 'http://localhost:8080/images/PauseButton.png';")
            window.evaluate_js("document.getElementById('audio').play();")
            self.is_playing = True
            print("playing :)")

    def play_song(self, url):
        window.evaluate_js(f"document.getElementById('audio').src = '{url}'")
        window.evaluate_js(f"document.getElementById('audio').play()")

    def add_to_queue(self, url):
        print(f"added {url} to the queue")
        self.song_queue.put(url)

    def play_next_in_queue(self):

        print("song finished")
        next_song_url = self.song_queue.get()

        self.play_song(next_song_url)
        self.populate_player_view(next_song_url)

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





