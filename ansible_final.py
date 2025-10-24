from pathlib import Path
import subprocess
import restconf_final

STUDENT_ID = getattr(restconf_final, "STUDENT_ID", "66070014")

def showrun(router_ip=None):
    """Get running configuration from router using Ansible"""
    playbook = Path("playbook.yaml")
    
    # Map IP to router name
    router_map = {
        "10.0.15.61": "CSR1KV-Pod1-1",
        "10.0.15.62": "CSR1KV-Pod1-2",
        "10.0.15.63": "CSR1KV-Pod1-3",
        "10.0.15.64": "CSR1KV-Pod1-4",
        "10.0.15.65": "CSR1KV-Pod1-5",
    }
    
    # Default to 10.0.15.65 if no IP provided (backward compatibility)
    if router_ip is None:
        router_ip = "10.0.15.65"
    
    router_name = router_map.get(router_ip, "CSR1KV-Pod1-5")
    output_file = Path(f"show_run_{STUDENT_ID}_{router_name}.txt")

    if not playbook.exists():
        return {"status": "FAIL", "msg": "Error: Ansible"}

    # Run ansible playbook with router IP filter
    r = subprocess.run(
        ["ansible-playbook", str(playbook), 
         "-e", f"router_ip={router_ip}"],
        capture_output=True, 
        text=True
    )
    print(r.stdout + r.stderr)

    if r.returncode or "failed=0" not in r.stdout + r.stderr or not output_file.exists():
        return {"status": "FAIL", "msg": "Error: Ansible"}

    return {"status": "OK", "msg": "show running config", "path": str(output_file)}


def set_motd(router_ip, motd_message):
    """Configure MOTD banner using Ansible"""
    playbook = Path("motd_playbook.yaml")
    
    if not playbook.exists():
        return {"status": "FAIL", "msg": "Error: Ansible"}
    
    # Escape quotes in motd_message
    motd_escaped = motd_message.replace('"', '\\"')
    
    # Run ansible playbook with extra variables
    r = subprocess.run(
        ["ansible-playbook", str(playbook), 
         "-e", f"router_ip={router_ip}",
         "-e", f'motd_message="{motd_escaped}"'],
        capture_output=True, 
        text=True
    )
    print(r.stdout + r.stderr)
    
    if r.returncode or "failed=0" not in r.stdout + r.stderr:
        return {"status": "FAIL", "msg": "Error: Ansible"}
    
    return {"status": "OK", "msg": "Ok: success"}


if __name__ == "__main__":
    showrun()
