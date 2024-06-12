# -*- coding: utf-8 -*-
__author__ = 'Miguel Freire Couy'
__credits__ = ['Miguel Freire Couy']
__maintainer__ = 'Miguel Freire Couy'
__email__ = 'miguel.couy@outlook.com'
__status__ = 'Production'

import os
import datetime as dt
from datetime import timezone

from pathlib import Path
import json
from typing import Literal, Optional
import pandas as pd
from urllib.error import HTTPError
import requests

from settings import (
    settings, FILES, PRECIPITATION_SOURCES, FORECAST_MODELS, MODES
)

SCRIPT_NAME = Path(os.path.basename(__file__))
SCRIPT_DIR = Path(os.path.dirname(__file__))
SCRIPT_RUN = dt.datetime.now().strftime('%Y-%m-%d %Hh%Mm%Ss')
SCRIPT_CONFIG: dict = settings
GLOBAL_CONFIG: dict = SCRIPT_CONFIG['global_config']

TOKEN_FILEPATH = Path(SCRIPT_DIR, '.pluvia')
BASE_URL = 'https://api.pluvia.app'

DATA_FOLDERPATH = Path(SCRIPT_DIR, 'data')
os.makedirs(DATA_FOLDERPATH, exist_ok = True)


access_token: dict = None
login_data: dict = None


# ----------------------------------------------------------------------
# Client authentication function | Função de autenticação do cliente
# ----------------------------------------------------------------------
def authenticate(
        _username: Optional[str] = None, 
        _password: Optional[str] = None,
        _data: Optional[dict] = None,
        headers: Optional[dict] = None,
        verify: Optional[bool] = None,
        token_filepath: Optional[Path] = None
        ) -> str:

    """
    This function authenticates a user by either finding a valid token in the
    specified file or refreshing it if necessary. It uses provided credentials
    or data to obtain a new token if the existing one is invalid or expired.

    Parameters:
    - `_username` (Optional[str]): The username for authentication.
      Required if `data` is not provided.
    - `_password` (Optional[str]): The password for authentication.
      Required if `data` is not provided.
    - `_data` (Optional[dict]): The data to be sent in the JSON body of the
      request. Defaults to None.
    - `headers` (Optional[dict]): The headers to be included in the request.
      Defaults to a JSON content type.
    - `verify` (Optional[bool]): A boolean indicating whether to verify the
      server's TLS certificate. Defaults to True.
    - `token_filepath` (Optional[Path]): The path to the file where the token
      data will be saved. Defaults to TOKEN_FILEPATH.

    Returns:
        dict[str]: A dictionary containing the token data.
    """

    if not _data and _username and _password:
        _data = {
            'username': _username,
            'password': _password
        } 

    if not headers:
        headers = {
            'content-type': 'application/json',
            'accept': '*/*'
        }

    if not verify:
        verify = True

    if not token_filepath:
        token_filepath = TOKEN_FILEPATH

    def find_token(token_filepath: Path) -> Optional[dict]:
        """
        This function checks if the token specified file exists. If it does, it
        reads the content and loads it as a dictionary using the `json` module.

        Parameters:
        - `token_filepath` (Path): The path to the JSON file containing the
          token.

        Returns:
            Optional[dict]: A dictionary containing the token data if the file
            exists and is valid JSON, otherwise None.
        """
        token_data: dict = None

        if token_filepath.exists():
            with open(token_filepath, '+r') as file:
                token_data: dict = json.loads(file.read())

        return token_data
    
    def is_valid_token(token: Optional[dict]) -> bool:
        """
        This function checks if the provided token is valid. It compares the 
        token's expiration date with the current date and time.

        Parameters:
        - `token` (Optional[dict]): A dictionary containing the token data, 
          which includes an 'expires' field with the expiration date in the 
          format '%Y-%m-%dT%H:%M:%SZ'.

        Returns:
            bool: True if the token is valid (i.e., the expiration date is in 
            the future), otherwise False.
        """
        if token:
            dt_to_expire = dt.datetime.strptime(
                token['expires'], '%Y-%m-%dT%H:%M:%SZ'
            ).replace(tzinfo = timezone.utc)

            dt_now = dt.datetime.now(timezone.utc)

            return dt_to_expire > dt_now
        
        else:
            return False

    def refresh_token(
            _data: dict,
            headers: dict,
            verify: bool
            ) -> dict:
        """
        This function refreshes the token by sending a POST request to the
        pluvia token endpoint. It includes the provided data and headers in the
        request.

        Parameters:
        - `_data` (dict): The data to be sent in the JSON body of the request.
        - `headers` (dict): The headers to be included in the request.
        - `verify` (bool): A boolean indicating whether to verify the server's
          TLS certificate.

        Returns:
            dict: A dictionary containing the new token data.

        Raises:
            HTTPError: If the request to refresh the token fails.
        """
    
        endpoint = '/v2/token'

        resp_token = requests.post(
            url = BASE_URL + endpoint, 
            headers = headers, 
            json = _data,
            verify = verify
        )
        
        resp_token.raise_for_status()

        token = json.loads(resp_token.content)

        return token

    def save_token(
            token: dict, 
            token_filepath: Path
            ) -> None:
        """
        This function saves the provided token dictionary to a specified file
        in JSON format.

        Parameters:
        - `token` (dict): The token data to be saved.
        - `token_filepath` (Path): The path to the file where the token data
          will be saved.

        Returns:
            None
        """
        with open(token_filepath, mode = '+w') as file:
            json.dump(token, file, indent = 4)

    global access_token
    global login_data

    token = find_token(
        token_filepath = token_filepath
    )

    if not is_valid_token(token):
        token = refresh_token(
           _data = _data, 
           headers = headers, 
           verify = verify
        )
    
        save_token(
            token = token,
            token_filepath = token_filepath
        )

    access_token = token['access_token']
    login_data = _data


# ----------------------------------------------------------------------
# Basic requisition functions | Função de requisições básicas
# ----------------------------------------------------------------------
def request_info_from_api(
        endpoint: str = None,
        headers: Optional[dict] = None, 
        verify: Optional[bool] = None
        ) -> Optional[dict]:
    
    authenticate(_data = login_data)
    
    if not endpoint:
        return None
    
    if not headers:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            "Content-Type": "application/json"
        }
    
    if not verify:
        verify = True

    response = requests.get(
        url = BASE_URL + endpoint, 
        headers = headers, 
        verify = verify
    )
    
    response.raise_for_status()

    return json.loads(response.content)

def request_file_from_api(
        endpoint: str = None,
        headers: Optional[dict] = None,
        verify: Optional[bool] = None,
        save_it: Optional[bool] = None,
        filename: Optional[str] = None, 
        filepath: Optional[Path] = None
        ) -> None:
    
    authenticate(_data = login_data)
    
    if not endpoint:
        return None
    
    if not headers:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            "Content-Type": "application/json"
        }
    
    if not verify:
        verify = True
    
    response = requests.get(
        url = BASE_URL + endpoint,
        headers = headers,
        verify = True
    )

    response.raise_for_status()

    if save_it:
        with open(Path(filepath, filename), 'wb') as file:
            for chunk in response.iter_content(chunk_size = 1024):
                file.write(chunk)


# ----------------------------------------------------------------------
# Basic requisition functions | Função de requisições básicas
# ----------------------------------------------------------------------
def get_id(this_name: str, list_dict: list[dict]) -> str:
    """
    Retrieve the ID from a list of dictionaries based on the 'descricao' key.

    Parameters:
    - `this_name` (str): The description to search for.
    - `list_dict` (List[Dict[str, Union[str, int]]]): The list of dictionaries to search.

    Returns:
        str: The ID associated with the given description.
    """
    return next(i['id'] for i in list_dict if i['descricao'] == this_name)

def fetch_ids(endpoint: str) -> list[dict]:
    return request_info_from_api(endpoint=endpoint)

def get_id_of_item(item_name: str, endpoint: str) -> str:
    """
    Retrieve the ID of a specific item by fetching data from the specified endpoint.

    Parameters:
    - `item_name` (str): The name of the item to retrieve the ID for.
    - `endpoint` (str): The API endpoint to fetch data from.

    Returns:
        str: The ID of the specified item.
    """
    return get_id(item_name, fetch_ids(endpoint))

def get_id_of_mode(mode: MODES) -> str:
    return get_id_of_item(mode, '/v2/valoresParametros/modos')

def get_id_of_precipitation_source(precipitation_source: PRECIPITATION_SOURCES) -> str:
    return get_id_of_item(precipitation_source, '/v2/valoresParametros/mapas')

def get_id_of_forecast_model(forecast_model: FORECAST_MODELS) -> str:
    return get_id_of_item(forecast_model, '/v2/valoresParametros/modelos')

authenticate(_username = 'miguel.couy', _password = '!Pluv14!')


print(get_id_of_mode(mode = 'Diário'))