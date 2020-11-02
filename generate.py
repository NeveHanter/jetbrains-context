import contextlib
import dataclasses
import operator
import os
import pathlib
import re
from typing import Optional, List, Tuple


@dataclasses.dataclass(frozen=True)
class AppDefinition:
    app_name: str
    app_id: str
    app_executable: str


APP_DEFINITIONS = (
    AppDefinition("CLion", "CLion", "clion64.exe"),
    AppDefinition("IntelliJ IDEA", "IDEA-U", "idea64.exe"),
    AppDefinition("PyCharm", "PyCharm-P", "pycharm64.exe"),
    AppDefinition("Rider", "Rider", "rider64.exe"),
)
REG_TEMPLATE = """Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Classes\\*\\shell\\Open with &{app_name}]
@=\"Open with &{app_name}\"
\"Icon\"=\"{app_executable_path}\"
[HKEY_CURRENT_USER\\Software\\Classes\\*\\shell\\Open with &{app_name}\\command]
@=\"\\\"{app_executable_path}\\\" \\\"%1\\\"\"

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\Open with &{app_name}]
@=\"Open with &{app_name}\"
\"Icon\"=\"{app_executable_path}\"
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\Open with &{app_name}\\command]
@=\"\\\"{app_executable_path}\\\" \\\"%1\\\"\"

[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\Open with &{app_name}]
@=\"Open with &{app_name}\"
\"Icon\"=\"{app_executable_path}\"
[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\Open with &{app_name}\\command]
@=\"\\\"{app_executable_path}\\\" \\\"%V\\\"\"
"""
VERSION_REGEXP = re.compile(r"^\d+\.\d+\.\d+$")


def get_latest_binary_path(app_definition: AppDefinition) -> Optional[pathlib.Path]:
    profile_path = pathlib.Path(os.environ["USERPROFILE"])
    channel_path = profile_path / "scoop" / "persist" / "jetbrains-toolbox" / "apps" / app_definition.app_id / "ch-0"

    versions = {}
    for path in channel_path.iterdir():
        if not path.is_dir():
            continue

        if VERSION_REGEXP.match(path.name):
            versions[tuple(map(int, path.name.split(".")))] = path

    if not versions:
        return None

    latest_version = sorted(versions.items(), key=operator.itemgetter(0), reverse=True)[0][1]
    
    return latest_version / "bin" / app_definition.app_executable


def main() -> None:
    with contextlib.suppress(FileExistsError):
        os.mkdir("out")

    for ad in APP_DEFINITIONS:
        reg_path = pathlib.Path("out", f"{ad.app_executable}-install-context.reg")
        if reg_path.exists():
            reg_path.unlink()

        app_executable_path = get_latest_binary_path(ad)
        if not app_executable_path:
            print(f"{ad.app_name} not detected.")

            continue

        content = REG_TEMPLATE.format(app_executable_path=str(app_executable_path).replace("\\", "\\\\"), app_name=ad.app_name)
        with reg_path.open("w", encoding="utf-8") as file:
            file.write(content)


if __name__ == '__main__':
    main()
