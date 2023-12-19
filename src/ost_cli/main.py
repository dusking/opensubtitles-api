"""
This file is part of Opensubtitles API wrapper.

Opensubtitles API is free software: you can redistribute it and/or modify
it under the terms of the MIT License as published by the Massachusetts
Institute of Technology.

For full details, please see the LICENSE file located in the root
directory of this project.
"""

import sys
import getpass
import logging
import argparse
from typing import List
from pathlib import Path

from opensubtitlescom import Config, OpenSubtitles, FileUtils
from .table import dict_to_pt

logger = logging.getLogger(__name__)

APP_NAME = "opensubtitlescom_py"
APP_VER = "0.1.3"
API_KEY = "CFpwJe7burdfYLEoTzSNG88Z7Lc2ex3b"
API_APP = f"{APP_NAME} v{APP_VER}"


def _get_api(cfg: Config):
    """Create an OpenSubtitles API object and login with the credentials in the config file."""
    subtitles = OpenSubtitles(API_APP, API_KEY)
    if cfg.username and cfg.password:
        subtitles.login(cfg.username, cfg.password)
    return subtitles


def set_credentials(args: argparse.Namespace):
    """Set the username and password in the config file."""
    cfg = Config(args.config)
    entered_username = input("Enter your username (leave blank to keep existing): ")
    if entered_username.strip():
        cfg.username = entered_username
    entered_password = getpass.getpass("Enter your password (leave blank to keep existing): ")
    if entered_password.strip():
        cfg.password = entered_password
    if cfg.save():
        print("Credentials set successfully")


def hide_secret(secret, show_chars=2):
    """Hide most characters in the middle of the secret value.

    Args:
        secret (str): The secret to be hidden.
        show_chars (int): The number of characters to reveal at the beginning and end.

    Returns:
        str: The password with hidden characters.
    """
    if not secret:
        return ""
    if len(secret) <= show_chars * 2:
        return secret  # Not enough characters to hide

    hidden_part = "*" * (len(secret) - show_chars * 2)
    hidden_password = secret[:show_chars] + hidden_part + secret[-show_chars:]
    return hidden_password


def show_credentials(args: argparse.Namespace):
    """Show the username and password in the config file."""
    cfg = Config(args.config)
    values = {
        "username": cfg.username,
        "password": hide_secret(cfg.password, 2),
        "language": cfg.language,
    }
    print(dict_to_pt(values, align="l"))


def download(args: argparse.Namespace):
    """
    Download a subtitle by file-id or moviehash
    """
    cfg = Config(args.config)
    api = _get_api(cfg)

    if args.file_id:
        srt = Path(args.file_id).with_suffix(".srt")
        with open(srt, "wb") as fp:
            fp.write(api.download(file_id=args.file_id))
    elif args.file:
        # Given a local file, search for the hash and download the first result,
        # eg "ost download --file mymovie.mp4" will download the subtitle for
        # mymovie.mp4 and save it as mymovie.srt
        mov = Path(args.file)
        srt = mov.with_suffix(".srt")
        fu = FileUtils(mov)
        h = fu.get_hash()
        response = api.search(moviehash=h, languages=cfg.language)
        if not response.data:
            print(f"No subtitles found for {mov}")
            return
        print(f"Found {len(response.data)} subtitles, downloading the first into {srt}")
        with open(srt, "wb") as fp:
            fp.write(api.download(file_id=response.data[0].file_id))
            


def parse_args(argv: List[str]):
    """Parse command-line arguments for the OpenSubtitles CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default="~/.config/opensubtitlescom/config.json", help="Path to the configuration file"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity level")

    subparsers = parser.add_subparsers(dest="command")

    set_credentials_parser = subparsers.add_parser("set-cred", help=set_credentials.__doc__)
    set_credentials_parser.set_defaults(command=set_credentials)

    set_credentials_parser = subparsers.add_parser("show-cred", help=show_credentials.__doc__)
    set_credentials_parser.set_defaults(command=show_credentials)

    download_parser = subparsers.add_parser("download", help=download.__doc__)
    download_parser.set_defaults(command=download)
    download_parser.add_argument("--file-id", type=int, help="Download a specific OSC file by ID")
    download_parser.add_argument("--file", type=Path, help="Download the subtitles for a local file")

    return parser.parse_args(argv)


def main():
    """Parse command line arguments and executes the specified command."""
    args = parse_args(sys.argv[1:])
    logging.basicConfig(
        level=logging.WARNING - (args.verbose * 10),
        format="%(asctime)s %(message)s",
    )
    if args.command:
        return args.command(args)
    else:
        print("No command given, use --help for usage")


if __name__ == "__main__":
    main()
