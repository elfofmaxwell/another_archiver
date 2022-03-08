import argparse
import sqlite3
import yaml

from channel_records import *
from fetch_video_list import *
from download_functions import *

def sync_config_db(): 
    try: 
        # get recorded channel list in config file
        with open('config.yaml') as f: 
            conf = yaml.safe_load(f)
        config_channel_list = set(conf['channels'])
        
        # get channels in channel_list table
        conn = sqlite3.connect('archive.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS channel_list (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, channel_id TEXT NOT NULL UNIQUE, channel_name TEXT NOT NULL, description TEXT NOT NULL, thumb_url TEXT NOT NULL, checkpoint_idx INTEGER NOT NULL DEFAULT 0)')
        cur.execute('SELECT channel_id FROM channel_list')
        searched_channel_list = cur.fetchall()
        if searched_channel_list: 
            db_channel_list = set([i[0] for i in searched_channel_list])
        else: 
            db_channel_list = set()
        
        # get unique channels
        config_unique_channels = config_channel_list - db_channel_list
        db_unique_channels = db_channel_list - config_channel_list
        
        # adding channels to config file
        if db_unique_channels: 
            for channel in db_unique_channels: 
                conf['channels'].append(channel)
        
        # adding channels to channel_list
        if config_unique_channels: 
            for channel in config_unique_channels: 
                init_channel(channel)
        
        return 0
    
    except: 
        raise

    finally: 
        cur.close()
        conn.commit()
        conn.close()

        
def main(): 
    # parser
    parser = argparse.ArgumentParser(description="Download videos of a Youtube channel")
    # channel id, optional
    parser.add_argument("--channel_id", "-c", type=str, default='', help='channel id for operation. If not provided when used to download, all channels would be downloaded')
    # choose one action, download or edit
    action_choice = parser.add_mutually_exclusive_group(required=True)
    action_choice.add_argument("--start", "-s", action="store_true", help="Start download with given channel id if the id is specified, or download all channels")
    action_choice.add_argument("--edit_checkpoint", "-e", action="store_true", help="Edit checkpoint for a given channel. Channel id must be specified")
    action_choice.add_argument("--fetch", "-f", action="store_true", help="Only update database without doing anything else")
    # auto download option
    parser.add_argument("--auto", action="store_true", help="Keep downloading without asking for next step")
    # choose one checkpoint edition method: index, video id, offset
    checkpoint_update_method = parser.add_mutually_exclusive_group()
    checkpoint_update_method.add_argument("--index", default=0, type=int, help="move checkpoint to this upload index")
    checkpoint_update_method.add_argument("--vid", default='', type=str, help="move checkpoint to this video")
    checkpoint_update_method.add_argument("--offset", default=0, type=int, help="move checkpoint by this offset")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase output verbosity")
    args = parser.parse_args()
    
    # update database
    sync_config_db()
    fetch_all()

    # edit checkpoint
    if args.edit_checkpoint: 
        # check whether channel id provided
        if not args.channel_id: 
            print("error: channel id required for editing checkpoint")
            return 1
        # edit checkpoint
        update_result = update_checkpoint(args.channel_id, args.index, args.vid, args.offset)
        if update_result != 1: 
            print('Update failed! Please check your args for moving checkpoint. ')
            return -1
        return 0
    
    # download
    elif args.start: 
        download_result = -1
        # if no channel id provided, download all channel
        if not args.channel_id: 
            download_result = download_channels(auto_continue=args.auto, verbosity=args.verbosity)
        # download specified channel
        else: 
            download_result = download_list(channel_id=args.channel_id, auto_continue=args.auto, verbosity=args.verbosity)
        
        return 0
    
    # fetch only
    elif args.fetch: 
        return 0
    
    else: 
        return -1



if __name__ == "__main__": 
    main()


