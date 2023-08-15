import datetime
import email
import imaplib
import os
from email.message import Message
from typing import List, Optional

from dotenv import load_dotenv

# Check if the file exists
if os.path.exists("expenses/.env"):
    load_dotenv(dotenv_path="expenses/.env")


class GmailClient:
    """
    This class is the client to connect to the Gmail server.
    It allows to obtain the emails from the specified email address.
    """

    def __init__(self, email):
        self._email = email
        self.conn = None

    def _connect(self, token: str) -> None:
        """
        This function connects to the IMAP server using the provided token.

        Parameters
        ----------
        token : str
            The app token generated by Gmail.

        Returns
        -------
        imaplib.IMAP4_SSL or None
            The connection to the IMAP server. If the connection fails, None
        """
        self.conn = imaplib.IMAP4_SSL("imap.gmail.com")
        try:
            self.conn.login(os.getenv("EMAIL"), token)
        except imaplib.IMAP4.error as e:
            print(f"Error connecting to IMAP server: {e}")

    def _obtain_emails_ids(
        self,
        email_from: str,
        most_recents_first: True,
        date_to_search: Optional[datetime.datetime] = None,
    ) -> List[str]:
        """
        This function obtains the ids of the emails from the specified email
        address.

        Parameters
        ----------
        email_from : str
            The email address to obtain the emails from.

        most_recents_first: bool
            If True, obtain the most recent email. If False, obtain the
            messages from the beginning.

        date: datetime.datetime, optional
            The date to obtain the emails from.
            If None, obtain all the emails. The function receives a datetime
            object, but it only uses the date part.

        Returns
        -------
        List[str]
            The ids of the emails from the specified email address.
        """
        if self.conn is None:
            self._connect(os.getenv("GMAIL_TOKEN"))

        self.conn.select("Inbox")
        query_search = f'(FROM "{email_from}")'

        # Check if the date is not None and is a datetime object
        if date_to_search is not None and isinstance(
            date_to_search, datetime.datetime
        ):
            # Format the date to the format that Gmail uses
            date_to_search = date_to_search.strftime("%d-%b-%Y")
            query_search = (
                f'(FROM "{email_from}") (SINCE "{date_to_search}")'
            )

        _, msgs_ids = self.conn.search(None, query_search)

        # The msgs ids are returned as a list of bytes, so we need to decode
        # them to strings
        msgs_ids = [msg_id.decode("utf-8") for msg_id in msgs_ids[0].split()]

        if most_recents_first:
            msgs_ids.reverse()

        return msgs_ids

    def obtain_emails(
        self,
        email_from: str,
        most_recents_first: True,
        limit: int = None,
        date_to_search: Optional[datetime.datetime] = None,
    ) -> List[Message]:
        """
        This function obtains the emails from the specified email address.

        Parameters
        ----------
        email_from : str
            The email address to obtain the emails from.

        most_recents_first: bool
            If True, obtain the most recent email. If False, obtain the
            messages from the beginning.

        limit: int, optional
            The maximum number of emails to obtain. If None, obtain all the
            emails.

        date: datetime.datetime, optional
            The date to obtain the emails from.

        Returns
        -------
        List[Message]
            The emails from the specified email address.
        """
        if self.conn is None:
            self._connect(os.getenv("GMAIL_TOKEN"))

        # Obtain the ids of the emails
        msgs_ids = self._obtain_emails_ids(
            email_from, most_recents_first, date_to_search
        )
        limit = len(msgs_ids) if limit is None else limit

        messages = []
        # Loop over the ids of the emails and obtain the messages
        for message_id in msgs_ids[:limit]:
            _, message_response = self.conn.fetch(message_id, "(RFC822)")
            for response in message_response:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    messages.append(msg)

        return messages
