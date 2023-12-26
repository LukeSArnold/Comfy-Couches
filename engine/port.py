import os
import sys
import eyed3
import spotipy
import sys
from requests import get
from spotipy.oauth2 import SpotifyClientCredentials

class Port:
    def __init__(self):
        pass 

    def get_artist_image(self, name, corresponding_song, corresponding_album, save_location):
        print("GETTING ARTIST IMAGE")

        cid = "8cdb42bee2324b83b78f517d35e59f61"
        secret = "c762f709fba64df091734eca9f126059"
        client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
        spotify = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

        artist_uri = spotify.search(f"{corresponding_song}{corresponding_album}{name}")["tracks"]["items"][0]["album"]["artists"][0]["uri"]

        artist_id = str(artist_uri.split(":")[-1])

        artists_result = spotify.artist(artist_id)

        img_url = artists_result["images"][0]["url"]

        img_data = get(img_url).content
        with open(f'{save_location}/artist_image.jpg', 'wb') as handler:
            handler.write(img_data)

    def port(self):
        cur_directory = os.path.dirname(os.path.realpath(__file__))
    
        music_dir = f"{cur_directory}/../Music/Music/"
        auto_add_dir = f"{cur_directory}/../Music/Automatically Add To Music"

        # files = []
        # for (dir_path, dir_names, file_names) in os.walk(auto_add_dir):
        #     files.extend(file_names)

        files = os.listdir(auto_add_dir)

        all_files = []
        for file in files:
            if ".mp3" in file[-4:]:
                all_files.append(f"{auto_add_dir}/{file}")

        for file in all_files:
            audio = eyed3.load(file)
            
            artist = audio.tag.artist

            if os.path.exists(f"{music_dir}/{artist}"):
                pass            
            else:
                os.mkdir(f"{music_dir}/{artist}")

            album = audio.tag.album

            if os.path.exists(f"{music_dir}/{artist}/{album}"):
                pass
            else:
                os.mkdir(f"{music_dir}/{artist}/{album}")

            song_name = audio.tag.title

            song_num = audio.tag.track_num[0]

            if song_num:
                if ((song_num/10) < 1):
                     song_num = f"0{song_num}"

            else:
               song_num = ""

            new_song_name = f"{song_num} {song_name}.mp3"

            if not os.path.isfile(f"{music_dir}/{artist}/{album}/{new_song_name}"):
                os.replace(file, f"{music_dir}/{artist}/{album}/{new_song_name}") 

            if not os.path.isfile(f"{music_dir}/{artist}/{album}/cover.jpg"):
                for image in audio.tag.images:
                    image_file = open(f"{music_dir}/{artist}/{album}/cover.jpg", "wb")
                    image_file.write(image.image_data)
                    image_file.close()
            if os.path.exists(f"{music_dir}/{artist}/artist_image.jpg"):
                pass
            else:
                self.get_artist_image(artist, song_name, album, f"{music_dir}/{artist}")
        
if __name__ == "__main__":
    porter = Port()
    porter.port()
