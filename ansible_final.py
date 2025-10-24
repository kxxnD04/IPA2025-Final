from pathlib import Path
import subprocess
import restconf_final

STUDENT_ID = getattr(restconf_final, "STUDENT_ID", "66070014")
ROUTER_NAME = "CSR1KV-Pod1-5"

def showrun():
    playbook = Path("playbook.yaml")
    output_file = Path(f"show_run_{STUDENT_ID}_{ROUTER_NAME}.txt")

    if not playbook.exists():
        return {"status": "FAIL", "msg": "Error: Ansible"}

    r = subprocess.run(["ansible-playbook", str(playbook)], capture_output=True, text=True)
    print(r.stdout + r.stderr)

    if r.returncode or "failed=0" not in r.stdout + r.stderr or not output_file.exists():
        return {"status": "FAIL", "msg": "Error: Ansible"}

    return {"status": "OK", "msg": "show running config", "path": str(output_file)}

if __name__ == "__main__":
    showrun()
