from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

device = { "device_type": "cisco_ios", "ip": "10.0.15.65", "username": "admin", "password": "cisco", "conn_timeout": 25, "banner_timeout": 120, "auth_timeout": 25, "global_delay_factor": 2, "fast_cli": False, }

def gigabit_status():
    try:
        with ConnectHandler(**device) as ssh:
            result = ssh.send_command("show ip interface brief", use_textfsm=True)
            if not isinstance(result, list):  # fallback if TextFSM fails
                result = [
                    {"interface": line.split()[0], "status": line.split()[4]}
                    for line in ssh.send_command("show ip interface brief").splitlines()
                    if line and not line.lower().startswith("interface")
                ]

            up = down = admin_down = 0
            statuses = []
            for r in result:
                name, status = r["interface"], r["status"].lower()
                statuses.append(f"{name} {status}")
                if status == "up":
                    up += 1
                elif status == "down":
                    down += 1
                elif "administratively down" in status:
                    admin_down += 1

            return f"{', '.join(statuses)} -> {up} up, {down} down, {admin_down} administratively down"

    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        return f"Error: Netmiko ({e})"
