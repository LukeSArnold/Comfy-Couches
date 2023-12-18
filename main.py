import random
import sys
import threading
import time
import webview
import os
import http.server
import socketserver
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import html

class Api:
    def __init__(self):
        self.cancel_heavy_stuff_flag = False

    def convert(self):
        print("boy howdy")

    def get_artists(self):
        reqs = requests.get('http://localhost:8080/Music/Music')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        urls = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href[0] != ".":
                urls.append(href) 

        for url in urls:
        
            artist_name = url.replace("%20", " ")

            javascript_code = """
                new_tag = document.createElement('div');
                new_tag.setAttribute('class', 'song-tag');

                new_tag.addEventListener('click', function(){
                    populate_artist_work('%s');
                });

                artist_name_element = document.createElement('h2');
                artist_name_element.innerText = '%s';

                document.getElementById('item-container').appendChild(new_tag);

                new_tag.appendChild(artist_name_element);
            """ % (url, artist_name)

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

            album_name = embed_url.replace("%20", " ")

            navigation_url = f"{url}{embed_url}"
           
            javascript_code = """
                new_tag = document.createElement('div');
                new_tag.setAttribute('class', 'song-tag');

                new_tag.addEventListener('click', function(){
                    populate_songs_from_album('%s');
                });

                album_name_element = document.createElement('h2');
                album_name_element.innerText = '%s';

                document.getElementById('item-container').appendChild(new_tag);

                new_tag.appendChild(album_name_element);
           """ % (navigation_url, album_name)

            window.evaluate_js(javascript_code)

    def populate_songs_from_album(self, url):
        reqs = requests.get(f'http://localhost:8080/Music/Music/{url}')
        soup = BeautifulSoup(reqs.text, 'html.parser')

        albums = []
        for link in soup.find_all('a'):
            href = link.get('href')
            albums.append(href)

        #clear div content
        window.evaluate_js("document.getElementById('item-container').innerHTML = ''")

        for embed_url in albums:

            album_name = BeautifulSoup(embed_url, "html.parser")

            #album_name = html.unescape(embed_url).replace("%20"," ")
            #album_name = embed_url.replace("%20", " ")

            navigation_url = f"http://localhost:8080/Music/Music/{url}{embed_url}"
            
            javascript_code = """
                new_tag = document.createElement('div');
                new_tag.setAttribute('class', 'song-tag');

                new_tag.addEventListener('click', function(){
                    play_song('%s');
                });

                album_name_element = document.createElement('h2');
                album_name_element.innerText = '%s';

                document.getElementById('item-container').appendChild(new_tag);

                new_tag.appendChild(album_name_element);
           """ % (navigation_url, album_name)

            window.evaluate_js(javascript_code)



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





