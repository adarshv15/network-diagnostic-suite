import subprocess

def traceroute(host):

    try:
        result = subprocess.run(
            ["tracert", "-d", "-h", "15", "-w", "500", host],
            capture_output=True,
            text=True
        )

        lines = result.stdout.split("\n")

        hops = []

        for line in lines:
            if line.strip().startswith(tuple(str(i) for i in range(1, 31))):
                hops.append(line.strip())

        return hops

    except Exception as e:
        return [f"Traceroute error: {e}"]