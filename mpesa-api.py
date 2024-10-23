import base64
import requests
import logging
import yaml

from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - mpesa-api - %(levelname)s - %(message)s')

global_config = {}


def get_auth_token():
    password = global_config["consumerKey"] + ":" + global_config["consumerSecret"]

    base64_string = base64_encode_string(password)

    headers = {
        "Authorization": "Basic " + base64_string,
        "Accept": "application/json"
    }

    params = {
        "grant_type": "client_credentials"
    }

    response = requests.get(global_config["url"], headers=headers, params=params)

    if response.status_code == 200:
        logging.info("Token generation Successful ")
    else:
        logging.error(f"Failed to fetch Data, Status Code: {response.status_code}")

    return response.json().get('access_token')


def stk_push_request(amount, customer_number):
    access_token = get_auth_token()
    timestamp = generate_timestamp()

    if not isinstance(amount, int):
        return {"error": "Invalid input: 'amount' must be an integer."}

    if not isinstance(customer_number, int):
        return {"error": "Invalid input: 'phone_number' must be an integer."}

    headers = {
        "Authorization": "Bearer " + access_token,
        "Accept": "application/json"
    }

    cust_number = parse_phone_number(customer_number)
    if cust_number.startswith("Invalid"):
        return "Invalid Customer Number"

    # CustomerPayBillOnline - Paybill Numbers | CustomerBuyGoodsOnline - For Till Numbers
    data = {
        "BusinessShortCode": global_config["businessShortCode"],
        "Password": str(generate_encrypting_password(timestamp)),
        "Timestamp": str(timestamp),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": int(cust_number),
        "PartyB": int(global_config["businessShortCode"]),
        "PhoneNumber": int(cust_number),
        "CallBackURL": str(global_config["callBackUrl"]),
        "AccountReference": "CompanyXLTD",
        "TransactionDesc": "Payment of X"

    }

    # print(f"Body: {data}")
    logging.info(f"Sending POST request to {global_config['stkpush_url']}")
    logging.info(f"Headers: {headers}")
    logging.info(f"Body: {data}")

    response = requests.post(global_config["stkpush_url"], json=data, headers=headers)

    if response.status_code == 200:
        logging.info(f"Response Data: {response.json()}")
    else:
        logging.info(f"Failed to send POST request. Status code: {response.status_code}")
        logging.info("Response Data: " + response.json().get("errorMessage"))

    return response.json()


def base64_encode_string(plain_string):
    plain_string_bytes = plain_string.encode("utf-8")
    base64_bytes = base64.b64encode(plain_string_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


def generate_encrypting_password(timestamp):
    encrypt_password = base64_encode_string(
        str(global_config["businessShortCode"]) + global_config["passKey"] + timestamp)
    return encrypt_password


def generate_timestamp():
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    return timestamp


def parse_phone_number(phone_number):
    phone_number_str = str(phone_number)

    if phone_number_str.startswith('0'):
        if len(phone_number_str) == 10:
            return '254' + phone_number_str[1:]
        else:
            return "Invalid: Number starting with '0' must be 10 digits long."
    elif phone_number_str.startswith('254'):
        if len(phone_number_str) == 12:
            return phone_number_str
        else:
            return "Invalid: Number starting with '254' must have exactly 12 digits."
    else:
        return "Invalid: Number must start with '0' or '254'."


def fetch_yaml_from_github(repo_url):
    """
    Fetches the YAML configuration file from a GitHub repository.
    :param repo_url: The raw URL of the YAML file in the GitHub repo.
    :return: Parsed YAML content as a dictionary, or None if an error occurs.
    """
    try:
        # Make a GET request to fetch the raw YAML file from GitHub
        response = requests.get(repo_url)

        # Raise an exception if the request failed
        response.raise_for_status()

        # Parse the YAML content
        yaml_content = yaml.safe_load(response.text)

        return yaml_content

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch YAML file from GitHub: {e}")
        return None

    except yaml.YAMLError as e:
        logging.error(f"Failed to parse YAML content: {e}")
        return None


def parse_config_values(github_raw_url):
    config = fetch_yaml_from_github(github_raw_url)

    global_config["url"] = config["mpesa"]["api"]["auth"]["url"]
    global_config["stkpush_url"] = config["mpesa"]["api"]["stkPush"]["url"]
    global_config["consumerKey"] = config["mpesa"]["api"]["consumerKey"]
    global_config["consumerSecret"] = config["mpesa"]["api"]["consumerSecret"]
    global_config["businessShortCode"] = config["mpesa"]["api"]["businessShortCode"]
    global_config["callBackUrl"] = config["mpesa"]["api"]["callbackUrl"]
    global_config["passKey"] = config["mpesa"]["api"]["passKey"]

    print(global_config)



