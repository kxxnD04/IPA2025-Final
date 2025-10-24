from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


def gigabit_status(router_ip):
    device = { "device_type": "cisco_ios", "ip": router_ip, "username": "admin", "password": "cisco", "conn_timeout": 25, "banner_timeout": 120, "auth_timeout": 25, "global_delay_factor": 2, "fast_cli": False, }
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


def get_motd(router_ip):
    """Get MOTD banner from router using Netmiko"""
    device = { "device_type": "cisco_ios", "ip": router_ip, "username": "admin", "password": "cisco", "conn_timeout": 25, "banner_timeout": 120, "auth_timeout": 25, "global_delay_factor": 2, "fast_cli": False, }
    
    try:
        with ConnectHandler(**device) as ssh:
            # Use simple show banner motd command
            result = ssh.send_command("show banner motd").strip() 
            # Check if MOTD is configured
            if not result or "not configured" in result.lower():
                return "Error: No MOTD Configured"
            return result
    
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        return f"Error: Netmiko ({e})"
    except Exception as e:
        print(f"Error getting MOTD: {e}")
        return "Error: Netmiko"
