# another_archiver

Another ytb_archiver with some unnecessary functions (to me) removed. Use sqlite rather than plaintext to store data for better performance and better searching functions. Use yaml config file rather than json for readability. Improve argparse. 

## Usage

Firstly obtain a oauth secrete from your google api client (see here: [Obtaining authorization credentials](https://developers.google.com/youtube/registering_an_application)); put the secrete file in the working directory. Then edit the config file (rename it to `config.yaml`) for channels, download path, slow mode, slow mode time, and cookie path. Then use `archive_cli.py` to download videos. 

```bash
archive_cli.py

usage: archiver_cli.py [-h] [--channel_id CHANNEL_ID] (--start | --edit_checkpoint | --fetch) [--auto]
                       [--index INDEX | --vid VID | --offset OFFSET]

Download videos of a Youtube channel

options:
  -h, --help            show this help message and exit
  --channel_id CHANNEL_ID, -c CHANNEL_ID
                        channel id for operation. If not provided when used to download, all channels would be downloaded
  --start, -s           Start download with given channel id if the id is specified, or download all channels
  --edit_checkpoint, -e
                        Edit checkpoint for a given channel. Channel id must be specified
  --fetch, -f           Only update database without doing anything else
  --auto                Keep downloading without asking for next step
  --index INDEX         move checkpoint to this upload index
  --vid VID             move checkpoint to this video
  --offset OFFSET       move checkpoint by this offset
  -v, --verbosity       increase output verbosity
  ```