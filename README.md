# Telegram Bulk Downloader

A Python script to bulk download files, photos, shared links, and GIFs from Telegram groups that the authenticated user is part of.

## Features

- Download multiple types of media: photos, documents, links, and GIFs
- Filter downloads by date range
- Filter downloads by message content
- Extract links from messages and web pages
- Unlimited download option (use `--limit 0`)
- Skip already downloaded files to avoid duplicates

## Requirements

- Python 3.6+
- Telegram API credentials (API ID and API Hash)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/telegram_bulk_downloader.git
   cd telegram_bulk_downloader
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   ```
   cp .env.local.example .env.local
   ```
   Then edit the `.env.local` file with your Telegram API credentials.

## How to Get Telegram API Credentials

1. Visit [https://my.telegram.org/apps](https://my.telegram.org/apps) and log in with your Telegram account.
2. Fill in the form with any name and select "Desktop" as the platform.
3. Click on "Create application" to get your `api_id` and `api_hash`.
4. Add these credentials to your `.env.local` file.

## Usage

### List Available Groups/Channels

```
python telegram_downloader.py --list
```

This will display all groups and channels you are a member of, along with their IDs.

### Download Media from a Group/Channel

```
python telegram_downloader.py --download --entity-id YOUR_GROUP_ID
```

### Additional Options

- `--media-type`: Specify the type of media to download (`all`, `photos`, `documents`, `links`, `gifs`)
  ```
  python telegram_downloader.py --download --entity-id YOUR_GROUP_ID --media-type photos
  ```

- `--limit`: Maximum number of messages to process (default: 100)
  ```
  python telegram_downloader.py --download --entity-id YOUR_GROUP_ID --limit 500
  ```

- `--days`: Only download media from the last N days
  ```
  python telegram_downloader.py --download --entity-id YOUR_GROUP_ID --days 7
  ```

- `--contains`: Only download media from messages containing specific text
  ```
  python telegram_downloader.py --download --entity-id YOUR_GROUP_ID --contains "vacation"
  ```

- `--download-dir`: Specify a custom download directory
  ```
  python telegram_downloader.py --download --entity-id YOUR_GROUP_ID --download-dir "my_downloads"
  ```

## Examples

1. Download all photos from a group posted in the last 30 days:
   ```
   python telegram_downloader.py --download --entity-id 123456789 --media-type photos --days 30
   ```

2. Extract all links from a channel with a limit of 1000 messages:
   ```
   python telegram_downloader.py --download --entity-id -1001234567890 --media-type links --limit 1000
   ```

3. Download all GIFs containing the word "funny":
   ```
   python telegram_downloader.py --download --entity-id 123456789 --media-type gifs --contains "funny"
   ```

## Security Notes

- The `.env.local` file containing your API credentials is excluded from git via `.gitignore`.
- Your session file (`telegram_downloader_session`) contains your authentication data and should be kept secure.
- Never share your `api_id` and `api_hash` with others.

## License

MIT
