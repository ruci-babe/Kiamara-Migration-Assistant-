# Kiamira

A lightweight Python CLI tool to export installed packages and selected files from one Linux distro, then generate an install plan for another distro.

## Features

- Auto-detects the source Linux distribution using `/etc/os-release`
- Exports installed packages for supported distros
- Copies user files and configuration directories into a migration bundle
- Generates a target install script for `apt`, `dnf`, `pacman`, and `zypper`
- Supports package name translation via a JSON mapping file

## Supported source/target distros

- Debian / Ubuntu
- Fedora / CentOS / RHEL
- Arch Linux
- openSUSE

## Usage

### Launch interactive mode

Run the executable without arguments to select one of the actions with the arrow keys and Enter. Use the `Quit` option to exit without running a task:

```
./migrate.py
```

### Export current system state

The `export` command automatically scans the source computer for installed applications and copies user files into the migration bundle.

```
python3 migrate.py export --manifest migration-manifest.json --output-dir migration-data
```

To copy the entire home folder as well, use:

```
python3 migrate.py export --manifest migration-manifest.json --output-dir migration-data --include-home
```

This creates:

- `migration-manifest.json`
- `migration-data/` containing copied files

### Generate an install script for the target distro

```
python3 migrate.py plan migration-manifest.json --target-distro ubuntu --output install-ubuntu.sh
```

### Deploy the saved manifest to a target distro

```
python3 migrate.py deploy migration-manifest.json --target-distro ubuntu --save-script install-ubuntu.sh
```

This will generate and run the install command for the packages in the manifest. Use `--dry-run` to preview without executing.

### Build Windows executable

A Windows executable can be created with PyInstaller from PowerShell.

```powershell
py -3 -m pip install -r requirements-dev.txt
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build_windows_exe.ps1
```

The executable is written to `dist\windows\Kiamara.exe`.

### Run on Windows with PowerShell

Install Python 3.8 or newer, then run the PowerShell wrapper from this repository:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_windows.ps1 --help
.\run_windows.ps1 export --manifest migration-manifest.json --output-dir migration-data
```

Run `.\run_windows.ps1` without arguments to open the interactive text menu. Windows does not require any third-party Python packages; the wrapper uses the `py` launcher when available and falls back to `python`.

### Run directly from GitHub without installing

From PowerShell, paste this single command to download the program temporarily and launch it:

```powershell
irm https://raw.githubusercontent.com/ruci-babe/Kiamara-Migration-Assistant-/main/run_from_github.ps1 | iex
```

The launcher stores the manifest and copied migration files in `Documents\Kiamara-Migration`. If Python 3 is not already installed, it downloads the official Python embeddable runtime temporarily instead of requiring administrator access. After the program exits, it removes the downloaded Python runtime, program, and temporary folder; it does not remove anything in `Documents\Kiamara-Migration`.

This command runs the current `main` branch from GitHub with the current user’s permissions. Review `run_from_github.ps1` before using it if you need to verify downloaded code first; for higher assurance, use a pinned release and verify its checksum instead of executing a mutable branch directly.

### Copy arbitrary files to a bundle

```
python3 migrate.py copy --paths ~/.bashrc ~/.config --destination /tmp/migration-bundle
```

### Assess Windows programs for Linux migration

```
python3 migrate.py win2linux --target-distro ubuntu --programs-file windows-programs.txt --generate-report
```

This will create a report in `migration-data/windows-to-linux-report.txt` listing:

- programs with known Linux equivalents
- programs without a mapped equivalent

### Assess Linux programs for Windows migration

```
python3 migrate.py linux2win --target-platform windows11 --programs-file linux-programs.txt --generate-report
```

This will create a report in `migration-data/linux-to-windows-report.txt` listing:

- programs with known Windows equivalents
- programs without a mapped equivalent

If no `--programs-file` is provided, the interactive mode will prompt for program names.

### Generate a Ninite installer URL for Windows

You can generate a Ninite URL directly from the Linux program list using either `linux2win` or the new dedicated `ninite` command.

```
python3 migrate.py linux2win --target-platform windows11 --programs-file linux-programs.txt --ninite --ninite-output ninite-url.txt
```

or:

```
python3 migrate.py ninite --programs-file linux-programs.txt --output ninite-url.txt
```

This will print a Ninite bundle URL for supported Windows apps and save it to `ninite-url.txt`.

Example output:

```
Ninite installer URL:
https://ninite.com/firefox-git-vlc/
```

Ninite support is available for common Windows apps like Firefox, Chrome, VLC, Git, Python, Slack, Zoom, and more.

### Use a package translation map

Create a JSON file such as `package-map.json`:

```json
{
  "vim": "vim",
  "python3-pip": "python3-pip"
}
```

Then run:

```
python3 migrate.py plan migration-manifest.json --target-distro fedora --map package-map.json
```

## Notes

- The tool does not perform automatic package name translation across all distros; use a mapping file for custom translations.
- File copying preserves directory structure and symlinks.
- Migration bundles may contain credentials, browser data, SSH keys, and other private files when those paths are selected. Review the paths before exporting, protect the bundle, and delete it securely when it is no longer needed.
- Run the generated install script on the target host after copying the migration bundle and manifest.

## Requirements

- Python 3.8+
- Standard library only

## License

MIT
