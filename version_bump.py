import sys
import subprocess
import os

def bump_version(level):
    version_file = 'version.txt'
    if not os.path.exists(version_file):
        with open(version_file, 'w') as f:
            f.write("0.0.0")

    with open(version_file, 'r') as f:
        version = f.read().strip()

    major, func, minor = map(int, version.split('.'))

    if level == 'major':
        major += 1
        func = 0
        minor = 0
    elif level == 'function':
        func += 1
        minor = 0
    elif level == 'minor':
        minor += 1
    else:
        print("❌ Use: major, function, or minor")
        sys.exit(1)

    new_version = f"{major}.{func}.{minor}"
    with open(version_file, 'w') as f:
        f.write(new_version)

    return new_version

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: version_bump.exe [major|function|minor]")
        sys.exit(1)

    level = sys.argv[1]
    version = bump_version(level)

    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"update {version}"], check=True)

    print(f"✅ Auto-committed: update {version}")
