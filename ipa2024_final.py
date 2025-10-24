#######################################################################################
# Yourname: Karn Suddee
# Your student ID: 66070014
# Your GitHub Repo: https://github.com/kxxnD04/IPA2024-Final

#######################################################################################
# 1. Import libraries for API requests, JSON formatting, time, os, (restconf_final or netconf_final), netmiko_final, and ansible_final.

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests_toolbelt.multipart.encoder import MultipartEncoder  # type: ignore

import restconf_final
import netconf_final  # type: ignore
import netmiko_final  # type: ignore
import ansible_final  # type: ignore

#######################################################################################
# 2. Assign the Webex access token to the variable ACCESS_TOKEN using environment variables.

load_dotenv()

ACCESS_TOKEN = os.environ.get("WEBEX_TOKEN")
if not ACCESS_TOKEN:
    raise EnvironmentError("Environment variable WEBEX_TOKEN is required")

#######################################################################################
# 3. Prepare parameters get the latest message for messages API.

roomIdToGetMessages = os.environ.get("ROOM_ID")
if not roomIdToGetMessages:
    raise EnvironmentError("Environment variable ROOM_ID is required")

WEBEX_MESSAGES_URL = "https://webexapis.com/v1/messages"
STUDENT_ID = getattr(restconf_final, "STUDENT_ID", "66070014")
AUTH_HEADER = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
last_message_id = None
method_specified = None  # Will store "restconf" or "netconf"
ROUTER_IPS = ("10.0.15.61", "10.0.15.62", "10.0.15.63", "10.0.15.64", "10.0.15.65")
VALID_COMMANDS = ("create", "delete", "enable", "disable", "status", "gigabit_status", "showrun", "motd")

while 1:
    time.sleep(1)

    getParameters = {"roomId": roomIdToGetMessages, "max": 1} # get the latest message

    try:
        r = requests.get(
            WEBEX_MESSAGES_URL,
            params=getParameters,
            headers=AUTH_HEADER,
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"Error fetching messages: {exc}")
        continue

    if r.status_code != 200:
        raise Exception(
            "Incorrect reply from Webex Teams API. Status code: {}".format(r.status_code)
        )

    json_data = r.json()

    if not json_data.get("items"):
        print("There are no messages in the room yet.")
        continue

    message_info = json_data["items"][0]
    message_id = message_info.get("id")
    if message_id == last_message_id:
        continue  # ignore duplicate polling of the same message
    last_message_id = message_id

    message = message_info.get("text", "")
    print("Received message: " + message)

## 4. Provide the URL to the Webex Teams messages API, and extract location from the received message.

    normalized = message.strip()
    parts = normalized.split()
    if len(parts) < 2 or parts[0] != f"/{STUDENT_ID}": # check if the message starts with my student ID
        continue

    # Parse command structure: /{STUDENT_ID} [method/IP/command] [IP/command] [command]
    
    command = None
    ip = None
    responseMessage = None
    motd_message = None  # For MOTD command with message
    
    # Check if parts[1] is a method declaration
    if parts[1].lower() in ("restconf", "netconf"):
        if parts[1].lower() == "restconf":
            method_specified = "restconf"
            responseMessage = "Ok: Restconf"
        else:
            method_specified = "netconf"
            responseMessage = "Ok: Netconf"
        
        # If only method is specified, send response and continue
        if len(parts) == 2:
            pass  # Will send responseMessage below
        else:
            # More parts after method, continue parsing
            if len(parts) >= 3:
                # Check if parts[2] is IP
                if parts[2] in ROUTER_IPS:
                    ip = parts[2]
                    if len(parts) >= 4:
                        command = parts[3].lower()
                        # Check if it's MOTD with message
                        if command == "motd" and len(parts) >= 5:
                            motd_message = " ".join(parts[4:])
                    else:
                        responseMessage = "Error: No command found."
                else:
                    # parts[2] might be a command without IP
                    command = parts[2].lower()
                    ip = None
            else:
                responseMessage = None
    else:
        # No method in parts[1], check if it's IP or command
        if parts[1] in ROUTER_IPS:
            ip = parts[1]
            if len(parts) >= 3:
                command = parts[2].lower()
                # Check if it's MOTD with message
                if command == "motd" and len(parts) >= 4:
                    motd_message = " ".join(parts[3:])
            else:
                responseMessage = "Error: No command found."
        else:
            # parts[1] is likely a command
            command = parts[1].lower()
            ip = None
    
    print(f"Method: {method_specified}, IP: {ip}, Command: {command}, MOTD: {motd_message}")

#######################################################################################
# 5. Complete the logic for each command
    attachment_path = None
    if responseMessage is None:
        responseMessage = None

        
        # Check if method is specified for commands that need it
        if command and command in VALID_COMMANDS:
            # MOTD command doesn't require method
            if command == "motd":
                if not ip:
                    responseMessage = "Error: No IP specified"
                elif ip not in ROUTER_IPS:
                    responseMessage = "Error: No IP specified"
                elif motd_message:
                    # Set MOTD using Ansible
                    try:
                        response = ansible_final.set_motd(ip, motd_message)
                        responseMessage = response.get("msg", "Error: Ansible")
                    except Exception as exc:
                        print(f"Error setting MOTD: {exc}")
                        responseMessage = "Error: Ansible"
                else:
                    # Get MOTD using Netmiko
                    try:
                        responseMessage = netmiko_final.get_motd(ip)
                    except Exception as exc:
                        print(f"Error getting MOTD: {exc}")
                        responseMessage = "Error: Netmiko"
            # gigabit_status and showrun also don't require method
            elif command == "gigabit_status":
                try:
                    responseMessage = netmiko_final.gigabit_status(ip)
                except Exception as exc:
                    print(f"Error running gigabit_status: {exc}")
                    responseMessage = "Error: Netmiko"
            elif command == "showrun":
                if not ip:
                    responseMessage = "Error: No IP specified"
                elif ip not in ROUTER_IPS:
                    responseMessage = "Error: No IP specified"
                else:
                    try:
                        response = ansible_final.showrun(ip)
                        responseMessage = response.get("msg", "Error: Ansible")
                        if response.get("status") == "OK":
                            attachment_path = response.get("path")
                        print(responseMessage)
                    except Exception as exc:
                        print(f"Error running showrun: {exc}")
                        responseMessage = "Error: Ansible"
            # Other commands require method
            elif not method_specified:
                responseMessage = "Error: No method specified"
            elif not ip:
                responseMessage = "Error: No IP specified"
            elif ip not in ROUTER_IPS:
                responseMessage = "Error: No IP specified"
            elif command == "create":
                if method_specified == "restconf":
                    responseMessage = restconf_final.create(ip, method_specified.capitalize())
                elif method_specified == "netconf":
                    responseMessage = netconf_final.create(ip, method_specified.capitalize())
            elif command == "delete":
                if method_specified == "restconf":
                    responseMessage = restconf_final.delete(ip, method_specified.capitalize())
                elif method_specified == "netconf":
                    responseMessage = netconf_final.delete(ip, method_specified.capitalize())
            elif command == "enable":
                if method_specified == "restconf":
                    responseMessage = restconf_final.enable(ip, method_specified.capitalize())
                elif method_specified == "netconf":
                    responseMessage = netconf_final.enable(ip, method_specified.capitalize())
            elif command == "disable":
                if method_specified == "restconf":
                    responseMessage = restconf_final.disable(ip, method_specified.capitalize())
                elif method_specified == "netconf":
                    responseMessage = netconf_final.disable(ip, method_specified.capitalize())
            elif command == "status":
                if method_specified == "restconf":
                    responseMessage = restconf_final.status(ip, method_specified.capitalize())
                elif method_specified == "netconf":
                    responseMessage = netconf_final.status(ip, method_specified.capitalize())
        elif command:
            responseMessage = "Error: No command found."

    if not responseMessage:
        continue

#######################################################################################
# 6. Complete the code to post the message to the Webex Teams room.

    if attachment_path and not MultipartEncoder:
        responseMessage = "Error: Ansible"
        attachment_path = None

    file_handle = None
    if attachment_path and MultipartEncoder:
        file_path = Path(attachment_path)
        try:
            file_handle = file_path.open("rb")
        except OSError as exc:
            print(f"Error opening attachment: {exc}")
            responseMessage = "Error: Ansible"
            payload = json.dumps({"roomId": roomIdToGetMessages, "text": responseMessage})
            HTTPHeaders = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        else:
            encoder = MultipartEncoder(
                fields={
                    "roomId": roomIdToGetMessages,
                    "text": responseMessage,
                    "files": (file_path.name, file_handle, "text/plain"),
                }
            )
            payload = encoder
            HTTPHeaders = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": encoder.content_type,
            }
    else:
        postData = {"roomId": roomIdToGetMessages, "text": responseMessage}
        payload = json.dumps(postData)
        HTTPHeaders = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    try:
        r = requests.post(
            WEBEX_MESSAGES_URL,
            data=payload,
            headers=HTTPHeaders,
            timeout=10,
        )
    finally:
        if file_handle:
            file_handle.close()

    if r.status_code != 200:
        raise Exception(
            "Incorrect reply from Webex Teams API. Status code: {}".format(r.status_code)
        )
