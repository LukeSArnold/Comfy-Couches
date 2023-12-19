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

class Api:
    def __init__(self):
        self.cancel_heavy_stuff_flag = False

    def convert(self):
        print("boy howdy")

    def get_artists(self):
        reqs = requests.get('http://localhost:8080/Music/Music')
        soup = BeautifulSoup(reqs.text, 'html.parser')

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

        albums = []
        for link in soup.find_all('a'):
            href = link.get('href')
            albums.append(href)

        #clear div content
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

        songs = []
        for link in soup.find_all('a'):
            href = link.get('href')
            songs.append(href)

        #clear div content
        window.evaluate_js("document.getElementById('item-container').innerHTML = ''")

        for embed_url in songs:

            song_name = unquote(embed_url)

            if song_name[0] != ".":
      
                if song_name[-4:] == ".mp3":

                    navigation_url = f"http://localhost:8080/Music/Music/{url}{embed_url}"
           
                    song_name = song_name[:-4]
                    #song_name.split(" ")
                    #song_name = " ".join(song_name[1:])
 
                    javascript_code = """
                        new_tag = document.createElement('div');
                        new_tag.setAttribute('class', 'song-tag');

                        new_tag.addEventListener('click', function(){
                            play_song('%s');
                        });

                        album_name_element = document.createElement('h4');
                        album_name_element.innerText = '%s';

                        document.getElementById('item-container').appendChild(new_tag);

                        new_tag.appendChild(album_name_element);
                    """ % (navigation_url, song_name)

                    window.evaluate_js(javascript_code)

    def populate_player_view(self, url):

        new_url = "/".join(url.split("/")[:-1])
         
        mp3_url = url.split("/")[-1]
        song_name = (unquote(mp3_url))[:-4]

        artist_url = url.split("/")[-2]
        artist_name = unquote(artist_url)
        

        total_url = new_url+"/cover.jpg"

        window.evaluate_js(f"document.getElementById('song-display-cover').src = '{total_url}'")

        window.evaluate_js(f"document.getElementById('song-display-song-name').innerHTML = '{song_name}'")
        window.evaluate_js(f"document.getElementById('song-display-artist-name').innerHTML = '{artist_name}'")

 

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





