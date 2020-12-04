import time
from random import randint
from os import listdir, rename, remove
from pathlib import Path
import logging
from threading import Thread

import PySimpleGUI as sg

import instagram_private_api as API


logging.disable()
sg.theme('LightGrey1')

def handle_login(api: API.InstagramAPI) -> None:
    layout = [
        [sg.Text('Please enter Instagram credentials', font=('Helvetica 16'))],
        [sg.Text('Username:', font=('Helvetica 14'), size=(10, 1)), sg.InputText(font=('Helvetica 12'))],
        [sg.Text('Password:', font=('Helvetica 14'), size=(10, 1)), sg.InputText(font=('Helvetica 12'))],
        [sg.Button('Submit', font=(12)), sg.Button('Cancel', font=(12))]
    ]
    p = Path('credentials')
    if 'credentials.json' not in [f.name for f in p.iterdir()]:
        window = sg.Window('Login', layout)
        event, values = window.read()
        window.close()
        if event != sg.WIN_CLOSED and event != 'Cancel':
            logged = api.login(values[0], values[1])
            api.export_credentials(path='credentials')
            sg.popup('Successfully logged in', font=('Helvetica 16'))
            if logged: return True
            return False
        return False
    else:
        api.load_credentials('credentials/credentials.json')
        return True

def set_options(values):
    options = {}
    options['post_per_day'] = int(values[0])
    options['photo_dir'] = values[1]
    options['captions_path'] = values[2]
    options['hashtags'] = values[3]
    options['locations'] = values[4]
    API.export_json(options, '.options.json')
    options['captions'] = API.load_list(values[2])
    options['sleep'] = (24 / options['post_per_day']) * 3600
    options['photos'] = [f for f in Path(values[1]).iterdir()] if values[0] else None
    return options

def get_caption(captions, options):
    caption = captions.pop(randint(0, len(captions) - 1)) if captions else ''
    API.export_list(captions, options['captions_path'])
    return caption

def run(api, options, sleep):
    post_count = 0

    options['locations'] = [
        api.search_location(location)[0] 
        for location in options['locations'].split(',')
    ] if options['locations'] else []

    while post_count < len(options['photos']):
        photo = options['photos'].pop(randint(0, len(options['photos']) - 1))
        caption = get_caption(options['captions'], options)
        full_caption = f'{caption}\n\n{options["hashtags"]}'
        location = (options['locations'][randint(0, len(options['locations']) - 1)] 
                    if options['locations'] else None)
        media = API.LocalMedia(
            api, 
            media_path=photo, 
            caption=caption + f'\n\n{options["hashtags"]}',
            location=location.id
        )
        api.upload_media(media)
        remove(photo)
        print(f'Successfully uploaded "{photo.name}" with caption "{caption}"\n')
        print(f'Next upload in {round(options["sleep"] / 3600)} hours\n')
        post_count += 1
        sleep.sleep(options['sleep'])
        print(sleep.abort)
        if sleep.abort:
            print('Stopped program\n')
            break

def start_gui(api) -> None:
    options = (API.load_json('.options.json') or {
        'post_per_day': '',
        'photo_dir': '',
        'captions_path': '',
        'hashtags': '',
        'locations': ''
    })
    layout = [
        [
            sg.Text('Number of posts per day:', font=('Helvetica 14'), size=(20, 1)), 
            sg.InputText(default_text=options['post_per_day'], font=('Helvetica 12'))
        ],
        [
            sg.Text('Path to the photos folder:', font=('Helvetica 14'), size=(20, 1)), 
            sg.InputText(default_text=options['photo_dir'], font=('Helvetica 12')), sg.FolderBrowse()
        ],
        [
            sg.Text('Path to the caption file:', font=('Helvetica 14'), size=(20, 1)), 
            sg.InputText(default_text=options['captions_path'], font=('Helvetica 12')), sg.FileBrowse()
        ],
        [
            sg.Text('Hashtags:', font=('Helvetica 14'), size=(20, 1)), 
            sg.InputText(default_text=options['hashtags'], font=('Helvetica 12'))
        ],
        [
            sg.Text('Locations:', font=('Helvetica 14'), size=(20, 1)), 
            sg.InputText(default_text=options['locations'], font=('Helvetica 12'))
        ],
        [sg.Output(size=(110, 20), font=('Helvetica 14'))],
        [sg.Button('Start', font=(12)), sg.Button('Stop', font=(12))]
    ]
    window = sg.Window('Login', layout)
    thread = None
    sleep = API.Sleep()
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            if thread:
                sleep.wake()
                break
        elif event == 'Stop':
            if thread: sleep.wake()
        else:
            options = set_options(values)
            if options['post_per_day'] and options['photos']:
                print('Sarting program\n')
                thread = Thread(target=run, args=(api, options, sleep))
                thread.start()
            else:
                print(
                    'Error starting program. Please set the number of posts'
                    ' per day and the path to the photos folder. Or make sure'
                    'the photos folder is not empty.\n'
                )
    window.close()

if __name__ == '__main__':
    api = API.InstagramAPI(debug=True)
    if handle_login(api):
        start_gui(api)


