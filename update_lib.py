import subprocess
import importlib.metadata
from collections import defaultdict

def get_installed_packages():
    packages = defaultdict(list)
    for dist in importlib.metadata.distributions():
        packages[dist.metadata["Name"].lower()].append(dist.version)
    return packages

def upgrade_package(package_name):
    print(f"[INFO] Попытка обновить: {package_name}")
    try:
        result = subprocess.run(
            ["python", "-m", "pip", "install", "--upgrade", package_name],
            capture_output=True, text=True, check=True
        )
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Не удалось обновить {package_name}: {e.stderr.strip()}")
        return False, e.stderr.strip()

def main():
    print("[INFO] Сканирование установленных пакетов...")
    installed_packages = get_installed_packages()
    failed_packages = {}
    updated_packages = []

    seen = set()
    for package in sorted(installed_packages):
        if package in seen:
            continue
        seen.add(package)
        success, message = upgrade_package(package)
        if success:
            updated_packages.append(package)
        else:
            failed_packages[package] = message

    print("\n--- Обновленные библиотеки ---")
    for pkg in updated_packages:
        print(f"+ {pkg}")

    print("\n--- Не удалось обновить ---")
    for pkg, err in failed_packages.items():
        print(f"- {pkg}: {err}")

if __name__ == "__main__":
    main()
