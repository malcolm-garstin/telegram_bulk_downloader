#!/usr/bin/env python3
"""
Telegram Bulk Downloader

A script to bulk download files, photos, shared links, and GIFs from Telegram groups
that the authenticated user is part of.
"""

import os
import sys
import asyncio
import re
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Third-party imports
from telethon import TelegramClient, events, utils
from telethon.tl.types import (MessageMediaPhoto, MessageMediaDocument, 
                               MessageMediaWebPage, InputMessagesFilterPhotos,
                               InputMessagesFilterDocument, InputMessagesFilterUrl,
                               InputMessagesFilterGif, Message)
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables from .env.local
load_dotenv('.env.local')

# Get API credentials from environment variables
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')

# Default download directory
DEFAULT_DOWNLOAD_DIR = 'downloads'

class TelegramDownloader:
    def __init__(self, api_id: str, api_hash: str, phone: str, download_dir: str = DEFAULT_DOWNLOAD_DIR):
        """
        Initialize the TelegramDownloader with API credentials and download directory.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone: Phone number for authentication
            download_dir: Directory to save downloaded files
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.download_dir = download_dir
        self.client = TelegramClient('telegram_downloader_session', api_id, api_hash)
        
    async def connect(self) -> None:
        """
        Connect to Telegram and handle authentication.
        """
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone)
            try:
                print(f"A verification code has been sent to {self.phone}")
                code = input("Enter the verification code: ")
                await self.client.sign_in(self.phone, code)
            except SessionPasswordNeededError:
                # Two-step verification is enabled
                password = input("Enter your two-step verification password: ")
                await self.client.sign_in(password=password)
        
        print("Successfully authenticated with Telegram!")
    
    async def get_dialogs(self) -> List[Dict[str, Any]]:
        """
        Get a list of all dialogs (chats/groups) the user is part of.
        
        Returns:
            List of dialog information dictionaries
        """
        dialogs = await self.client.get_dialogs()
        return [
            {
                'id': dialog.id,
                'name': dialog.name,
                'type': 'Group' if dialog.is_group else 'Channel' if dialog.is_channel else 'Private'
            }
            for dialog in dialogs
        ]
    
    async def list_dialogs(self) -> None:
        """
        Display a list of all dialogs (chats/groups) the user is part of.
        """
        dialogs = await self.get_dialogs()
        
        print("\nAvailable Telegram Groups/Channels:")
        print("-" * 60)
        print(f"{'Index':<6} {'ID':<12} {'Type':<10} {'Name':<30}")
        print("-" * 60)
        
        for i, dialog in enumerate(dialogs, 1):
            print(f"{i:<6} {dialog['id']:<12} {dialog['type']:<10} {dialog['name']:<30}")
    
    async def download_media(self, entity_id: int, media_type: str = 'all', 
                          limit: Optional[int] = 100, offset_date: Optional[datetime] = None,
                          contains: Optional[str] = None) -> None:
        """
        Download media from a specific chat/group.
        
        Args:
            entity_id: ID of the chat/group
            media_type: Type of media to download ('all', 'photos', 'documents', 'links', 'gifs')
            limit: Maximum number of messages to process (None for unlimited)
            offset_date: Only download media after this date
            contains: Only download media from messages containing this text
        """
        entity = await self.client.get_entity(entity_id)
        entity_name = utils.get_display_name(entity)
        
        # Create download directory for this entity
        entity_dir = Path(self.download_dir) / f"{entity_name}_{entity_id}"
        entity_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nDownloading {media_type} from {entity_name}")
        print(f"Saving to: {entity_dir}")
        
        # Set up the appropriate filter based on media_type
        if media_type == 'photos':
            filter_type = InputMessagesFilterPhotos()
        elif media_type == 'documents':
            filter_type = InputMessagesFilterDocument()
        elif media_type == 'links':
            filter_type = InputMessagesFilterUrl()
        elif media_type == 'gifs':
            filter_type = InputMessagesFilterGif()
        else:  # 'all'
            filter_type = None
        
        # Get messages with the specified filter
        messages = await self.client.get_messages(
            entity,
            limit=limit,
            offset_date=offset_date,
            filter=filter_type
        )
        
        # Filter messages by content if specified
        if contains:
            messages = [msg for msg in messages if msg.text and contains.lower() in msg.text.lower()]
        
        if not messages:
            print("No matching messages found.")
            return
        
        print(f"Found {len(messages)} messages to process.")
        
        # Download media from messages
        downloaded_count = 0
        skipped_count = 0
        links_file = None
        
        if media_type == 'links' or media_type == 'all':
            links_file = open(entity_dir / 'extracted_links.txt', 'w', encoding='utf-8')
        
        for message in tqdm(messages, desc="Downloading"):
            try:
                # Handle different media types
                if message.media:
                    if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                        # Download photos and documents
                        if media_type in ['all', 'photos', 'documents', 'gifs']:
                            # Get the filename without downloading
                            attributes = getattr(message.media, 'document', None)
                            if attributes and hasattr(attributes, 'attributes'):
                                for attr in attributes.attributes:
                                    if hasattr(attr, 'file_name') and attr.file_name:
                                        potential_path = entity_dir / attr.file_name
                                        if potential_path.exists():
                                            print(f"Skipping existing file: {attr.file_name}")
                                            skipped_count += 1
                                            continue
                            
                            # Download if file doesn't exist
                            filename = await self.client.download_media(message, entity_dir)
                            if filename:
                                downloaded_count += 1
                    
                    elif isinstance(message.media, MessageMediaWebPage) and message.media.webpage.url:
                        # Extract links from web pages
                        if media_type in ['all', 'links'] and links_file:
                            links_file.write(f"{message.media.webpage.url}\n")
                            downloaded_count += 1
                
                # Extract URLs from message text
                if message.text and (media_type in ['all', 'links']) and links_file:
                    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.text)
                    for url in urls:
                        links_file.write(f"{url}\n")
                        downloaded_count += 1
            
            except Exception as e:
                print(f"Error processing message: {e}")
        
        if links_file:
            links_file.close()
        
        print(f"\nDownloaded/extracted {downloaded_count} items from {entity_name}.")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} already existing files.")

    async def close(self) -> None:
        """
        Disconnect from Telegram.
        """
        await self.client.disconnect()

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Telegram Bulk Downloader')
    parser.add_argument('--list', action='store_true', help='List available groups/channels')
    parser.add_argument('--download', action='store_true', help='Download media from a group/channel')
    parser.add_argument('--entity-id', type=int, help='ID of the group/channel to download from')
    parser.add_argument('--media-type', choices=['all', 'photos', 'documents', 'links', 'gifs'], 
                        default='all', help='Type of media to download')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of messages to process (0 for unlimited)')
    parser.add_argument('--days', type=int, help='Only download media from the last N days')
    parser.add_argument('--contains', type=str, help='Only download media from messages containing this text')
    parser.add_argument('--download-dir', type=str, default=DEFAULT_DOWNLOAD_DIR, 
                        help='Directory to save downloaded files')
    
    args = parser.parse_args()
    
    # Check if API credentials are set
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        print("Error: API credentials not found. Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, "
              "and TELEGRAM_PHONE_NUMBER in .env.local file.")
        return
    
    # Initialize the downloader
    downloader = TelegramDownloader(
        api_id=API_ID,
        api_hash=API_HASH,
        phone=PHONE_NUMBER,
        download_dir=args.download_dir
    )
    
    try:
        # Connect to Telegram
        await downloader.connect()
        
        if args.list:
            # List available groups/channels
            await downloader.list_dialogs()
        
        elif args.download:
            # Check if entity ID is provided
            if not args.entity_id:
                print("Error: --entity-id is required for downloading.")
                await downloader.list_dialogs()
                return
            
            # Calculate offset date if days is specified
            offset_date = None
            if args.days:
                offset_date = datetime.now() - timedelta(days=args.days)
            
            # Convert limit of 0 to None for unlimited downloads
            actual_limit = None if args.limit == 0 else args.limit
            
            # Download media
            await downloader.download_media(
                entity_id=args.entity_id,
                media_type=args.media_type,
                limit=actual_limit,
                offset_date=offset_date,
                contains=args.contains
            )
        
        else:
            # No action specified, show help
            parser.print_help()
    
    finally:
        # Disconnect from Telegram
        await downloader.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)