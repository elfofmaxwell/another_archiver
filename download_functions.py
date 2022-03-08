# -*- coding: utf-8 -*-
import subprocess
import os
import sqlite3
import yaml
import random
import time 

def single_download_cycle(channel_id: str, download_path: str, cookie_path='', verbosity=0): 
    try: 
        conn = sqlite3.connect('archive.db')
        cur = conn.cursor()
        
        # retrieve checkpoint from channel_list
        cur.execute('SELECT channel_name, checkpoint_idx FROM channel_list WHERE channel_id=?', (channel_id, ))
        searched_checkpoint_idx = cur.fetchall()
        if not searched_checkpoint_idx: 
            raise NameError('No valid channel data')
        channel_name = searched_checkpoint_idx[0][0]
        checkpoint_idx = searched_checkpoint_idx[0][1]

        # retrieve video data for download
        cur.execute('SELECT video_id, date, title FROM video_list WHERE channel_id=? and upload_idx=?', (channel_id, checkpoint_idx+1))
        searched_video_info = cur.fetchall()
        if not searched_video_info: 
            print("%s %s: all video downloaded" % (channel_name, channel_id))
            return 0
        video_info = {
            'url': 'https://www.youtube.com/watch?v='+searched_video_info[0][0], 
            'date_path': os.path.join(download_path, searched_video_info[0][1][:10])
        }
        
        # construct download target folder
        if not os.path.isdir(video_info['date_path']): 
            os.makedirs(video_info['date_path'])

        # construct argument for yt-dlp
        dlp_args = [
            'yt-dlp', 
            '--path', video_info['date_path'], 
            video_info['url']
        ]

        if os.path.isfile(cookie_path): 
            dlp_args.insert(-2, '--cookies')
            dlp_args.insert(-2, cookie_path)
        # run yt-dlp and display messages, save log if log option is on
        completed_dlp = subprocess.run(dlp_args, capture_output=True)
        dlp_stdout = completed_dlp.stdout.decode('utf-8')
        dlp_stderr = completed_dlp.stderr.decode('utf-8')
        if verbosity >= 2: 
            print(dlp_stdout, dlp_stderr)
        elif verbosity >= 1: 
            if dlp_stderr: 
                print(dlp_stderr)
            print("%s %s: %s %s on %s has finished. " % (channel_name, channel_id, searched_video_info[0][0], searched_video_info[0][2]))
        else: 
            if dlp_stderr: 
                print(dlp_stderr)

        # update checkpoint
        cur.execute('UPDATE channel_list SET checkpoint_idx=? WHERE channel_id=?', (checkpoint_idx+1, channel_id))
        return 1
    except: 
        raise
    finally: 
        cur.close()
        conn.commit()
        conn.close()


def download_list(channel_id: str, auto_continue=True, verbosity=0): 
    '''
    args: channel_id (str); auto_continue (Boolean); verbose (int)
    Download all videos in video_list for a given channel; if auto_continue is set to False, confirmation is required before next download and slow mode would not work
    '''
    # load config file
    with open('config.yaml') as f: 
        conf = yaml.safe_load(f)
    download_path = os.path.join(conf['download_path'], channel_id, 'by_upload_date')
    if not os.path.isdir(download_path): 
        os.makedirs(download_path)
    sleep_time = conf['sleep_time']
    slow_mode = conf['slow_mode']
    cookie_path = conf['cookie_path']
    
    # keep download until all videos downloaded or manually stopped
    while True: 
        # download
        continue_flag = single_download_cycle(channel_id, download_path, cookie_path, verbosity=verbosity)
        if not continue_flag: 
            return 0
        
        # ask for stop if not auto_continue
        if not auto_continue: 
            while True: 
                ask_continue = input('Continue? y|n')
                if ask_continue.lower() in ('y', 'n'): 
                    break
            if ask_continue.lower == 'n': 
                return 0
        # sleep if in slow mode
        if slow_mode and auto_continue: 
            sleep_length = random.randint(sleep_time-0.1*sleep_time, sleep_time+0.1*sleep_time)
            for i in range(sleep_length): 
                time.sleep(1)
    

def download_channels(auto_continue=True, verbosity=0): 
    try: 
        conn = sqlite3.connect('archive.db')
        cur = conn.cursor()

        # get channel list
        cur.execute('SELECT channel_id FROM channel_list')
        searched_channel_list = cur.fetchall()
        if not searched_channel_list: 
            raise NameError('No valid channel data')
        channel_list = [i[0] for i in searched_channel_list]

        for channel_id in channel_list: 
            download_list_result = download_list(channel_id, auto_continue=auto_continue, verbosity=verbosity)
        
        return 0

    except: 
        raise

    finally: 
        cur.close()
        conn.commit()
        conn.close()


