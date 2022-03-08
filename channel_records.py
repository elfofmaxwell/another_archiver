# -*- coding: utf-8 -*-

import json
import sqlite3
import sys
import os

import googleapiclient.discovery
import googleapiclient.errors
import google_auth_oauthlib

def init_channel(channel_id): 
    '''
    args: channel_id (str)
    Create channel_list table and fetch channel info from youtube; initialize checkpoint at 0 (meaningful checkpoint starting at 1)
    '''
    # set api credentials
    scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "secrets.json"
    refresh_token_file = "refresh_token.json"
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    # if no refresh token, request brand new token set
    if not os.path.isfile('refresh_token.json'): 
        credentials = flow.run_console()
        with open('refresh_token.json', 'w') as f: 
            json.dump(credentials.refresh_token, f)
    # if there is refresh token, use it to get new access token
    else: 
        with open(client_secrets_file) as f: 
            client_info = json.load(f)
        client_id = client_info["installed"]["client_id"]
        with open(refresh_token_file) as f: 
            refresh_token = json.load(f)
        flow.oauth2session.refresh_token(flow.client_config['token_uri'], refresh_token=refresh_token, client_id=client_id, client_secret=flow.client_config['client_secret'])
        credentials = google_auth_oauthlib.helpers.credentials_from_session(flow.oauth2session, flow.client_config)
    # create api client
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
    
    try: 
        # connect to db and create table for channel_list if not existing
        conn = sqlite3.connect('archive.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS channel_list (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, channel_id TEXT NOT NULL UNIQUE, channel_name TEXT NOT NULL, description TEXT NOT NULL, thumb_url TEXT NOT NULL, checkpoint_idx INTEGER NOT NULL DEFAULT 0)')

        # get channel detail
        request = youtube.channels().list(
            id = channel_id, 
            part = "snippet", 
            maxResults = 1
        )
        response = request.execute()
        channel_info = response['items'][0]['snippet']

        cur.execute('SELECT id FROM channel_list WHERE channel_id=?', (channel_id,))
        existing_id = cur.fetchall()
        
        if existing_id: 
            cur.execute('UPDATE channel_list SET channel_name=?, description=?, thumb_url=? WHERE id=?', (channel_info['title'], channel_info['description'], channel_info['thumbnails']["high"]["url"], existing_id[0][0]))
        else: 
            cur.execute('INSERT INTO channel_list (channel_id, channel_name, description, thumb_url) VALUES (?, ?, ?, ?)', (channel_id, channel_info['title'], channel_info['description'], channel_info['thumbnails']["high"]["url"]))
    
    except: 
        raise

    finally: 
        cur.close()
        conn.commit()
        conn.close()


def update_checkpoint(channel_id: str, checkpoint_idx=0, video_id='', offset=0): 
    '''
    args: channel_id (str); checkpoint_idx (int, key arg, optional); video_id(str, key arg, optional); offset (int, key arg, optional)
    move checkpoint for a given channel. Priority: checkpoint_idx > video_id > offset
    '''
    if (not checkpoint_idx) and (not video_id) and (not offset): 
        return -1
    try: 
        conn = sqlite3.connect('archive.db')
        cur = conn.cursor()

        if offset: 
            cur.execute('SELECT checkpoint_idx FROM channel_list WHERE channel_id=?', (channel_id,))
            old_checkpoint = cur.fetchall()[0][0]
            new_checkpoint_idx = old_checkpoint + offset

        if video_id: 
            cur.execute('SELECT upload_idx FROM video_list WHERE video_id=?', (video_id,))
            upload_idx_searching = cur.fetchall()
            if not upload_idx_searching: 
                return -1
            new_checkpoint_idx = upload_idx_searching[0][0]

        if checkpoint_idx: 
            new_checkpoint_idx = checkpoint_idx

        cur.execute('UPDATE channel_list SET checkpoint_idx=? WHERE channel_id=?', (new_checkpoint_idx, channel_id))
        return cur.rowcount

    except: 
        raise

    finally: 
        cur.close()
        conn.commit()
        conn.close()
        


def test(): 
    channel_id = sys.argv[1]
    init_channel(channel_id)

if __name__ == "__main__": 
    test()