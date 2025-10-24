import json
import requests

requests.packages.urllib3.disable_warnings()

STUDENT_ID = "66070014"
INTERFACE_NAME = f"Loopback{STUDENT_ID}"

HEADERS = {
	"Accept": "application/yang-data+json",
	"Content-Type": "application/yang-data+json",
}
AUTH = ("admin", "cisco")


def _get_urls(router_ip):
	"""Generate API URLs for the given router IP"""
	base_url = f"https://{router_ip}/restconf/data"
	api_url = f"{base_url}/ietf-interfaces:interfaces/interface={INTERFACE_NAME}"
	api_url_status = f"{base_url}/ietf-interfaces:interfaces-state/interface={INTERFACE_NAME}"
	return api_url, api_url_status


def _loopback_payload(enabled=True):
	last_three = STUDENT_ID[-3:] # รหัส นศ 3 ตัวท้าย
	octet_x = int(last_three[0]) # x คือเลขตัวแรก
	octet_y = int(last_three[1:]) # y คือเลขตัวที่สองและสาม
	ipv4_address = f"172.{octet_x}.{octet_y}.1"
	return {
		"ietf-interfaces:interface": {
			"name": INTERFACE_NAME,
			"description": f"Loopback interface for student id {STUDENT_ID}",
			"type": "iana-if-type:softwareLoopback",
			"enabled": enabled,
			"ietf-ip:ipv4": {
				"address": [
					{
						"ip": ipv4_address,
						"netmask": "255.255.255.0",
					}
				]
			},
			"ietf-ip:ipv6": {},
		}
	}

# Helpers Functions to check that loopback interface or any GigabitEthernet existence
def _interface_exists(router_ip):
	api_url, _ = _get_urls(router_ip)
	resp = requests.get(api_url, auth=AUTH, headers=HEADERS, verify=False)
	if resp.status_code == 200:
		return True
	if resp.status_code == 404:
		return False
	raise RuntimeError(f"RESTCONF lookup failed with status {resp.status_code}")


def create(router_ip, method="Restconf"):
	try:
		if _interface_exists(router_ip):
			return f"Cannot create: Interface {INTERFACE_NAME.lower()}"
	except RuntimeError as error:
		print(error)
		return "Error: RESTCONF create"

	api_url, _ = _get_urls(router_ip)
	payload = _loopback_payload(enabled=True)
	resp = requests.put(
		api_url,
		data=json.dumps(payload),
		auth=AUTH,
		headers=HEADERS,
		verify=False,
	)

	if 200 <= resp.status_code <= 299:
		print(f"STATUS OK: {resp.status_code}")
		return f"Interface {INTERFACE_NAME.lower()} is created successfully using {method}"

	print(f"Error. Status Code: {resp.status_code}")
	return "Error: RESTCONF create"


def delete(router_ip, method="Restconf"):
	try:
		if not _interface_exists(router_ip):
			return f"Cannot delete: Interface {INTERFACE_NAME.lower()}"
	except RuntimeError as error:
		print(error)
		return "Error: RESTCONF delete"

	api_url, _ = _get_urls(router_ip)
	resp = requests.delete(
		api_url,
		auth=AUTH,
		headers=HEADERS,
		verify=False,
	)

	if 200 <= resp.status_code <= 299:
		print(f"STATUS OK: {resp.status_code}")
		return f"Interface {INTERFACE_NAME.lower()} is deleted successfully using {method}"

	print(f"Error. Status Code: {resp.status_code}")
	return "Error: RESTCONF delete"


def enable(router_ip, method="Restconf"):
	try:
		if not _interface_exists(router_ip):
			return f"Cannot enable: Interface {INTERFACE_NAME.lower()}"
	except RuntimeError as error:
		print(error)
		return "Error: RESTCONF enable"

	api_url, _ = _get_urls(router_ip)
	payload = {"ietf-interfaces:interface": {"enabled": True}}
	resp = requests.patch(
		api_url,
		data=json.dumps(payload),
		auth=AUTH,
		headers=HEADERS,
		verify=False,
	)

	if 200 <= resp.status_code <= 299:
		print(f"STATUS OK: {resp.status_code}")
		return f"Interface {INTERFACE_NAME.lower()} is enabled successfully using {method}"

	print(f"Error. Status Code: {resp.status_code}")
	return "Error: RESTCONF enable"


def disable(router_ip, method="Restconf"):
	try:
		if not _interface_exists(router_ip):
			return f"Cannot shutdown: Interface {INTERFACE_NAME.lower()}"
	except RuntimeError as error:
		print(error)
		return "Error: RESTCONF disable"

	api_url, _ = _get_urls(router_ip)
	payload = {"ietf-interfaces:interface": {"enabled": False}}
	resp = requests.patch(
		api_url,
		data=json.dumps(payload),
		auth=AUTH,
		headers=HEADERS,
		verify=False,
	)

	if 200 <= resp.status_code <= 299:
		print(f"STATUS OK: {resp.status_code}")
		return f"Interface {INTERFACE_NAME.lower()} is shutdowned successfully using {method}"

	print(f"Error. Status Code: {resp.status_code}")
	return "Error: RESTCONF disable"


def status(router_ip, method="Restconf"):
	_, api_url_status = _get_urls(router_ip)
	resp = requests.get(
		api_url_status,
		auth=AUTH,
		headers=HEADERS,
		verify=False,
	)

	if 200 <= resp.status_code <= 299:
		print(f"STATUS OK: {resp.status_code}")
		response_json = resp.json()
		interface_data = response_json.get("ietf-interfaces:interface")

		if isinstance(interface_data, list):
			interface_data = interface_data[0]

		if not isinstance(interface_data, dict):
			return "Error: RESTCONF status"

		admin_status = interface_data.get("admin-status", "unknown")
		oper_status = interface_data.get("oper-status", "unknown")

		if admin_status == "up" and oper_status == "up":
			return f"Interface {INTERFACE_NAME.lower()} is enabled (checked by {method})"
		if admin_status == "down" and oper_status == "down":
			return f"Interface {INTERFACE_NAME.lower()} is disabled (checked by {method})"
		return (
			f"Interface {INTERFACE_NAME.lower()} admin-status={admin_status} "
			f"oper-status={oper_status} (checked by {method})"
		)

	if resp.status_code == 404:
		print(f"STATUS NOT FOUND: {resp.status_code}")
		return f"No Interface {INTERFACE_NAME.lower()} (checked by {method})"

	print(f"Error. Status Code: {resp.status_code}")
	return "Error: RESTCONF status"
