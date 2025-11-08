"""
Lookup module.

This module provides the `FileLookup` strategy for matching query strings
against entries stored in a text file. It supports two modes of operation:

- Cached lookups: Load all entries into memory once and query from cache.
- Memory-mapped lookups: Re-read the file on each query using `mmap`.

It also includes utility functions such as `sanitize_payload` for safely
decoding and cleaning raw byte input before performing lookups.
"""

from __future__ import annotations
import logging
from pathlib import Path
import subprocess
from typing import Optional
import mmap


def sanitize_payload(raw: bytes, strip_ctrl: bool = True) -> str:
    """
    Decode a raw byte payload into a clean string.

    The function attempts to decode the input bytes as UTF-8 while ignoring
    any undecodable sequences. It then strips trailing null characters and
    newlines, and optionally removes all non-printable (control) characters.

    Args:
        raw (bytes): The raw byte sequence to sanitize.
        strip_ctrl (bool): If True (default), non-printable
            characters (control chars) are removed from the decoded text.

    Returns:
        str: A sanitized string with nulls/newlines removed and optionally
        stripped of non-printable characters.
    """
    text = raw.decode("utf-8", errors="ignore").rstrip("\x00\r\n")
    if strip_ctrl:  # Remove control characters from the string
        text = "".join(ch for ch in text if ch.isprintable())
    return text.strip()


class FileLookup:
    """Lookup strategy that matches strings against lines in a text file."""
    def __init__(self, filepath: Path, reread_on_query: bool = False) -> None:
        self.filepath = Path(filepath)
        self.reread_on_query = reread_on_query
        self._cache: dict[str, bool] = self._read_file()

    def _read_file(self) -> dict[str, bool]:
        """
        Read the lookup file into memory and build a cache.

        Each line of the file is stripped of whitespace and stored as a key in
        a dictionary with the value set to True, \
            enabling O(1) membership checks.

        Returns:
            dict[str, bool]: A dictionary of lookup entries where keys are
            normalized lines from the file and values are always True.

        Notes:
            - If the file does not exist, an empty dictionary is returned and
            an error is logged.
            - If any other error occurs during reading, it is logged and an
            empty dictionary is returned.
        """
        try:
            lookup_table: dict[str, bool] = {}
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    key = line.strip()
                    # Build the cache with all string in the line as True
                    lookup_table[key] = True
            return lookup_table
        except FileNotFoundError:
            logging.error("Lookup file not found: %s", self.filepath)
            raise FileExistsError
        except Exception as e:
            logging.error("Error reading lookup file %s: %s", self.filepath, e)
            raise Exception

    def grep_search_m_1(self, query: bytes) -> bool:
        """
        Perform a full-line search in the file using \
            Linux ``grep``, stopping after the first match.

        This method uses the following grep flags:
            - ``-F``: Treat the query as a fixed string.
            - ``-x``: Match the entire line.
            - ``-q``: Suppress output (rely on exit code).
            - ``-m 1``: Stop searching after the first match.

        Args:
            self (FileLookup): \
                The lookup object holding the file path.
            query (bytes): The raw query string as bytes.

        Returns:
            Optional[bool]:
                - ``True`` if the query string was found.
                - ``False`` if the query string was not found.
                - ``None`` if an error occurred while executing grep.
        """
        query_str = sanitize_payload(query, strip_ctrl=True)
        command = ["grep", "-F", "-x", "-q", "-m", "1",
                   query_str, str(self.filepath)]
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            process.wait()
            result = (True, False)
            return result[process.returncode]
        except Exception as e:
            logging.error(f"Error: {e}")
            return False

    def grep_search(self, query: bytes) -> Optional[bool]:
        """
        Perform a full-line search in the file using \
            the native Linux ``grep`` command.

        This method uses the following grep flags:
            - ``-F``: Treat the query as a fixed string \
                (no regex interpretation).
            - ``-x``: Match the entire line (not substrings).
            - ``-q``: Suppress all output; \
                only the return code indicates match status.

        Args:
            self (FileLookup): The lookup object holding the file path.
            query (bytes): The raw query string as bytes.

        Returns:
            Optional[bool]:
                - ``True`` if the query string was found.
                - ``False`` if the query string was not found.
                - ``None`` if an error occurred while executing grep.
        """
        query_str = sanitize_payload(query, strip_ctrl=True)
        command = ["grep", "-F", "-x", "-q",
                   query_str, str(self.filepath)]
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            process.wait()
            result = (True, False)
            return result[process.returncode]  # 0 → True, 1 → False
        except Exception as e:
            logging.error(f"Error: {e}")
            return False

    def linear_search(self, query: bytes) -> bool:
        """
        Perform a manual linear search over the file contents.

        This method reads the file line by line, stripping whitespace,
        and checks for an exact match against the query string.

        Args:
            self (FileLookup): The lookup object holding the file path.
            query (bytes): The raw query string as bytes.

        Returns:
            bool:
                - ``True`` if the query string was found.
                - ``False`` if not found, or if an error occurred \
                    (e.g., file I/O error).
        """
        query_str = sanitize_payload(query, strip_ctrl=True)
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if query_str == line.strip():
                        return True
            return False
        except Exception as e:
            logging.error(f"Error: {e}")
            return False

    def search_awk(self, query: bytes) -> bool:
        """
        Perform a full-line search using the Linux ``awk`` command.

        The query string is passed safely into an ``awk`` expression that
        checks if the entire line equals the query.

        Args:
            self (FileLookup): The lookup object holding the file path.
            query (bytes): The raw query string as bytes.

        Returns:
            bool:
                - ``True`` if the query string was found.
                - ``False`` if not found, or if an error occurred \
                    (e.g., awk execution failure).
        """
        query_str = sanitize_payload(query, strip_ctrl=True)
        try:
            result = subprocess.run(
                ["awk", f'$0 == "{query_str}"', str(self.filepath)],
                capture_output=True,
                text=True,
                check=False,
            )
            return bool(result.stdout.strip())
        except Exception as e:
            logging.error(f"Error: {e}")
            return False

    def readlines_search(self, query: bytes) -> bool:
        """
        Perform a full-line search by reading the file into memory at once.

        This approach loads all lines into a list and \
            checks whether the query string
        plus a newline character exists in the list.\
            Suitable only for smaller files.

        Args:
            self (FileLookup): The lookup object holding the file path.
            query (bytes): The raw query string as bytes.

        Returns:
            bool:
                - ``True`` if the query string was found.
                - ``False`` if not found, or if an error occurred \
                    (e.g., file I/O error).
        """
        query_str = sanitize_payload(query, strip_ctrl=True)
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return f"{query_str}\n" in lines
        except Exception as e:
            logging.error(f"Error: {e}")
            return False

    def mmap_search(self, query: bytes) -> bool:
        """
        Perform a direct lookup of the query string \
            using memory-mapped file access.
        The query is sanitized with `sanitize_payload`, encoded, and checked
        against the contents of the lookup file using a memory map.
        This allows efficient searching without fully \
                loading the file into memory.

        Args:
            query (bytes): The raw query string to search for in the file.

        Returns:
            bool:
                - True if the sanitized query exists in the file.
                - False otherwise.
        """
        # Sanitize the query byte string
        sanitized_query = sanitize_payload(query, strip_ctrl=True)
        query = f"{sanitized_query}\n".encode()
        # Prepare a string to check the last line without next line
        last_query = sanitized_query.encode()
        try:
            with open(self.filepath, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    return query in mm[:] or last_query in mm[:]
        except Exception as e:
            logging.error(f"Error: {e}")
            return False

    def cache_lookup(self, query: bytes) -> bool:
        """
        Look up the given query in the in-memory cache.

        The query is first sanitized using `sanitize_payload` with control
        characters stripped, then checked against the cached lookup table
        populated from the file at initialization.

        Args:
            query (bytes): The raw query string to check.

        Returns:
            bool:
                - True if the sanitized query exists in the cache.
                - False otherwise.
        """

        query_str = sanitize_payload(query, strip_ctrl=True)
        return self._cache.get(query_str, False)

    def find_match(self, query: bytes) -> bool:
        """
        The main lookup function.

        Depending on the configuration, this method either:
        - Uses a cached lookup table (default), or
        - Re-reads the file and performs a memory-mapped search if
            `reread_on_query` is enabled.

        Args:
            query (bytes): The raw query string to search for. It will be
                sanitized before lookup.

        Returns:
            Optional[bool]:
                - True if the query matches an entry in the file.
                - False if the query does not match.
                - None if an error occurs during lookup.

        """
        if self.reread_on_query:
            return self.mmap_search(query=query)
        return self.cache_lookup(query=query)
