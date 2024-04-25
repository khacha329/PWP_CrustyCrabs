"""
This class is from the MusicMeta API client shown in exercise 4:
https://lovelace.oulu.fi/file-download/embedded/ohjelmoitava-web/ohjelmoitava-web/pwp-musicmeta-submit-script-py/
"""
import json


class APIError(Exception):
    """
    Exception class used when the API responds with an error code. Gives
    information about the error in the console.
    """

    def __init__(self, code, error, url):
        """
        Initializes the exception with *code* as the status code from the response
        and *error* as the response body.
        """

        self.error = json.loads(error)
        self.code = code
        self.url = url

    def __str__(self):
        """
        Returns all details from the error response sent by the API formatted into
        a string.
        """
        try:
            msgs = "\n".join(self.error["@error"]["@messages"])
            value = f'Error {self.code} while accessing {self.url}: ' \
                    f'{self.error["@error"]["@message"]}\n' \
                    f'Details:\n' \
                    f'{msgs}'
        except KeyError:
            value = f'Error {self.code} while accessing {self.url}: {self.error["message"]}'

        return value