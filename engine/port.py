import os
import sys
import eyed3
class Port:
    def __init__(self):
        pass 

    def port(self):
        cur_directory = os.path.dirname(os.path.realpath(__file__))
    
        music_dir = f"{cur_directory}/../Music/Music/"
        auto_add_dir = f"{cur_directory}/../Music/Automatically Add To Music"
      
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
                
        
if __name__ == "__main__":
    porter = Port()
    porter.port()
