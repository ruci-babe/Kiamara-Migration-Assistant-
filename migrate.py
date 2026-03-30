#!/usr/bin/env python3
import argparse
import curses
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_MANAGERS = {
    'debian': {'list': ['dpkg-query', '-W', '-f=${Package}\n'], 'install': 'apt-get install -y'},
    'ubuntu': {'list': ['dpkg-query', '-W', '-f=${Package}\n'], 'install': 'apt-get install -y'},
    'fedora': {'list': ['rpm', '-qa', '--qf', '%{NAME}\n'], 'install': 'dnf install -y'},
    'centos': {'list': ['rpm', '-qa', '--qf', '%{NAME}\n'], 'install': 'dnf install -y'},
    'rhel': {'list': ['rpm', '-qa', '--qf', '%{NAME}\n'], 'install': 'dnf install -y'},
    'arch': {'list': ['pacman', '-Qq'], 'install': 'pacman -S --noconfirm'},
    'opensuse': {'list': ['rpm', '-qa', '--qf', '%{NAME}\n'], 'install': 'zypper install -y'},
}

WINDOWS_LINUX_APP_MAP = {
    'google chrome': 'chromium',
    'chrome': 'chromium',
    'firefox': 'firefox',
    'microsoft edge': 'microsoft-edge-dev',
    'edge': 'microsoft-edge-dev',
    'vlc media player': 'vlc',
    'vlc': 'vlc',
    'notepad++': 'notepadqq',
    'notepadpp': 'notepadqq',
    '7-zip': 'p7zip',
    '7zip': 'p7zip',
    'putty': 'putty',
    'git': 'git',
    'python': 'python3',
    'python3': 'python3',
    'python2': 'python2',
    'spotify': 'spotify',
    'slack': 'slack',
    'skype': 'skypeforlinux',
    'zoom': 'zoom',
    'microsoft office': 'libreoffice',
    'office': 'libreoffice',
    'word': 'libreoffice-writer',
    'excel': 'libreoffice-calc',
    'powerpoint': 'libreoffice-impress',
    'adobe reader': 'evince',
    'adobe acrobat': 'evince',
    'photoshop': 'gimp',
    'illustrator': 'inkscape',
    'corel draw': 'inkscape',
    'notepad': 'gedit',
    'calculator': 'gnome-calculator',
}

LINUX_WINDOWS_APP_MAP = {
    'chromium': 'Microsoft Edge / Chrome',
    'firefox': 'Firefox',
    'vlc': 'VLC Media Player',
    'gimp': 'Adobe Photoshop / GIMP for Windows',
    'inkscape': 'Adobe Illustrator / Inkscape for Windows',
    'libreoffice': 'Microsoft Office',
    'libreoffice-writer': 'Microsoft Word',
    'libreoffice-calc': 'Microsoft Excel',
    'libreoffice-impress': 'Microsoft PowerPoint',
    'gedit': 'Notepad++ / Visual Studio Code',
    'git': 'Git for Windows',
    'python3': 'Python 3 for Windows',
    'python2': 'Python 2 for Windows',
    'putty': 'PuTTY for Windows',
    'spotify': 'Spotify for Windows',
    'slack': 'Slack for Windows',
    'zoom': 'Zoom for Windows',
}

NINITE_APP_MAP = {
    'chromium': 'chrome',
    'chrome': 'chrome',
    'firefox': 'firefox',
    'vlc': 'vlc',
    'gimp': 'gimp',
    'inkscape': 'inkscape',
    'libreoffice': 'libreoffice',
    'libreoffice-writer': 'libreoffice',
    'libreoffice-calc': 'libreoffice',
    'libreoffice-impress': 'libreoffice',
    'gedit': 'notepadplusplus',
    'notepadqq': 'notepadplusplus',
    'git': 'git',
    'python3': 'python',
    'python2': 'python',
    'putty': 'putty',
    'spotify': 'spotify',
    'slack': 'slack',
    'zoom': 'zoom',
    '7zip': '7zip',
    'p7zip': '7zip',
}

ANSI_PINK = '\033[95m'
ANSI_RESET = '\033[0m'

LOGO_LINES = [
    "  _  ___ _                       _                           __  __ _ _ _       ",
    " | |/ (_) |_ ___  __ _ _ __ ___ | | ___  _ __   ___  _ __   |  \\/  (_| (_) ___  ",
    " | ' /| | __/ _ / _` | '_ ` _ \\| |/ _ \\| '_ \\ / _ \\| '_ \\  | |/| | | |/ _ \\ ",
    " | . \\| | ||  __/ (_| | | | | | | | (_) | | | | (_) | | | | | |  | | | |  __/ ",
    " |_|\\_\\_|\\__\\___|\\__,_|_| |_| |_|_|\\___/|_| |_|\\___/|_| |_| |_|  |_|_|_|\\___| ",
    "                                                                                ",
    "                        Kiamara Migration Tool                                ",
]

DEFAULT_FILES = [
    '~/.bashrc',
    '~/.profile',
    '~/.config',
    '~/Documents',
    '~/Pictures',
    '~/.ssh',
]


class MigrationError(Exception):
    pass


def run_command(command):
    try:
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True)
        return output.strip().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise MigrationError(f"Failed to run command: {' '.join(command)} ({e})")


def execute_command(command, dry_run=False):
    print('Executing:', ' '.join(command))
    if dry_run:
        print('Dry run enabled, not executing install command.')
        return
    subprocess.run(command, check=True)


def get_package_install_command(target_distro, packages):
    if target_distro not in PACKAGE_MANAGERS:
        raise MigrationError(f"Unsupported target distro: {target_distro}")
    install_cmd = PACKAGE_MANAGERS[target_distro]['install']
    return shlex.split(install_cmd) + sorted(set(packages))


def deploy_manifest(manifest_path, target_distro, mapping=None, dry_run=False, save_script=None, force=False):
    manifest = load_json_file(manifest_path)
    packages = manifest.get('packages', [])
    if mapping is None:
        mapping = {}
    mapping = {str(k).strip().lower(): v for k, v in mapping.items()}
    translated = [mapping.get(pkg.lower(), pkg) for pkg in packages]

    if save_script:
        build_install_script(translated, target_distro, mapping=None, output_path=save_script)
        print(f"Deploy script saved to {save_script}")

    install_cmd = get_package_install_command(target_distro, translated)
    if dry_run:
        execute_command(install_cmd, dry_run=True)
    else:
        if not force:
            proceed = ask_bool('Proceed with deployment and install packages on the target distro?', False)
            if not proceed:
                raise MigrationError('Deployment cancelled by user.')
        execute_command(install_cmd, dry_run=False)
    return translated, install_cmd


def detect_distro():
    if os.path.isfile('/etc/os-release'):
        data = {}
        with open('/etc/os-release', 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if '=' in line:
                    key, value = line.rstrip().split('=', 1)
                    data[key] = value.strip('"')
        id_like = data.get('ID_LIKE', '').lower()
        distro_id = data.get('ID', '').lower()
        if distro_id in PACKAGE_MANAGERS:
            return distro_id
        if distro_id in ('linuxmint',):
            return 'ubuntu'
        if 'debian' in id_like:
            return 'debian'
        if 'fedora' in id_like or 'rhel' in id_like or 'centos' in id_like:
            return 'fedora'
        if 'arch' in id_like:
            return 'arch'
        if 'suse' in id_like:
            return 'opensuse'
    return platform.system().lower()


def list_installed_packages(source_distro):
    if source_distro not in PACKAGE_MANAGERS:
        raise MigrationError(f"Unsupported source distro: {source_distro}")
    command = PACKAGE_MANAGERS[source_distro]['list']
    return sorted(set(run_command(command)))


def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def build_install_script(packages, target_distro, mapping=None, output_path=None, show_progress=False):
    if target_distro not in PACKAGE_MANAGERS:
        raise MigrationError(f"Unsupported target distro: {target_distro}")
    if mapping is None:
        mapping = {}

    target_cmd = PACKAGE_MANAGERS[target_distro]['install']
    translated = []
    total = len(packages)
    for index, pkg in enumerate(packages, start=1):
        translated.append(mapping.get(pkg, pkg))
        if show_progress:
            print_progress_bar(index, total, prefix='Translating packages:', suffix='Complete', length=40)
    if show_progress:
        print()

    lines = [
        '#!/bin/sh',
        '# Generated package install plan',
        'set -e',
        'echo "Installing translated package list..."',
        f'{target_cmd} ' + ' '.join(sorted(set(translated))),
    ]
    script_text = '\n'.join(lines) + '\n'
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_text)
        os.chmod(output_path, 0o755)
    return script_text


def normalize_paths(paths):
    expanded = []
    for path in paths:
        if path.startswith('~'):
            path = os.path.expanduser(path)
        expanded.append(Path(path))
    return expanded


def scan_windows_installed_programs():
    try:
        command = [
            'powershell', '-NoProfile', '-Command',
            r"Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* , "
            r"HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* , "
            r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | "
            r"Where-Object { $_.DisplayName } | Select-Object -ExpandProperty DisplayName"
        ]
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True)
        programs = [line.strip() for line in output.splitlines() if line.strip()]
        return sorted(set(programs))
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            output = subprocess.check_output(['wmic', 'product', 'get', 'name'], stderr=subprocess.DEVNULL, text=True)
            programs = [line.strip() for line in output.splitlines()[1:] if line.strip()]
            return sorted(set(programs))
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise MigrationError(f'Unable to scan Windows installed programs: {exc}')


def scan_linux_installed_programs(source_distro):
    programs = list_installed_packages(source_distro)
    for tool, command in [('flatpak', ['flatpak', 'list', '--app', '--columns=application']),
                          ('snap', ['snap', 'list'])]:
        try:
            output = subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True)
            if tool == 'flatpak':
                programs += [line.strip() for line in output.splitlines() if line.strip()]
            else:
                lines = [line.strip().split()[0] for line in output.splitlines()[1:] if line.strip()]
                programs += lines
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return sorted(set(programs))


def scan_installed_programs(source_distro=None):
    system = platform.system()
    if system == 'Windows':
        return scan_windows_installed_programs()
    if system == 'Linux':
        if source_distro is None:
            source_distro = detect_distro()
        return scan_linux_installed_programs(source_distro)
    raise MigrationError(f'Automatic program scanning is not supported on {system}')


def load_program_list(path):
    path = Path(path).expanduser()
    if not path.exists():
        raise MigrationError(f"Programs file not found: {path}")
    if path.suffix.lower() == '.json':
        data = load_json_file(path)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
        raise MigrationError('Expected JSON array of program names in programs file.')
    text = path.read_text(encoding='utf-8', errors='ignore')
    return [line.strip() for line in text.splitlines() if line.strip()]


def ask_multiline(prompt):
    print(prompt)
    print('(Enter program names one per line; blank line to finish)')
    lines = []
    while True:
        value = input().strip()
        if not value:
            break
        lines.append(value)
    return lines


def build_windows_migration_report(programs, target_distro, mapping=None, output_dir=None, output_name='windows-to-linux-report.txt'):
    if mapping is None:
        mapping = {}
    mapping = {str(k).strip().lower(): v for k, v in mapping.items()}

    mapped = []
    unmapped = []
    for program in programs:
        key = program.strip().lower()
        if not key:
            continue
        linux_equiv = mapping.get(key) or WINDOWS_LINUX_APP_MAP.get(key)
        if linux_equiv:
            mapped.append((program.strip(), linux_equiv))
        else:
            unmapped.append(program.strip())

    report_lines = [
        f'Windows to Linux migration report for target distro: {target_distro}',
        f'Total programs analyzed: {len(mapped) + len(unmapped)}',
        f'Programs with known Linux equivalents: {len(mapped)}',
        f'Programs without known equivalents: {len(unmapped)}',
        '',
        '=== Can migrate / have Linux equivalents ===',
    ]
    for windows_name, linux_name in mapped:
        report_lines.append(f'- {windows_name} -> {linux_name}')
    report_lines.extend(['', '=== Cannot automatically migrate / unknown equivalents ==='])
    for windows_name in unmapped:
        report_lines.append(f'- {windows_name}')
    report_lines.extend([
        '',
        'Note: Unmapped programs may still be used on Linux via Wine, virtualization, or web alternatives.',
        'This report is a compatibility guideline, not an installer.',
    ])

    if output_dir:
        output_dir = Path(output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / output_name
        report_path.write_text('\n'.join(report_lines) + '\n', encoding='utf-8')
        print(f'Report written to {report_path}')
        return mapped, unmapped, report_path
    return mapped, unmapped, None


def build_linux_migration_report(programs, target_platform, mapping=None, output_dir=None, output_name='linux-to-windows-report.txt'):
    if mapping is None:
        mapping = {}
    mapping = {str(k).strip().lower(): v for k, v in mapping.items()}

    mapped = []
    unmapped = []
    for program in programs:
        key = program.strip().lower()
        if not key:
            continue
        windows_equiv = mapping.get(key) or LINUX_WINDOWS_APP_MAP.get(key)
        if windows_equiv:
            mapped.append((program.strip(), windows_equiv))
        else:
            unmapped.append(program.strip())

    report_lines = [
        f'Linux to Windows migration report for target platform: {target_platform}',
        f'Total programs analyzed: {len(mapped) + len(unmapped)}',
        f'Programs with known Windows equivalents: {len(mapped)}',
        f'Programs without known equivalents: {len(unmapped)}',
        '',
        '=== Can migrate / have Windows equivalents ===',
    ]
    for linux_name, windows_name in mapped:
        report_lines.append(f'- {linux_name} -> {windows_name}')
    report_lines.extend(['', '=== Cannot automatically migrate / unknown equivalents ==='])
    for linux_name in unmapped:
        report_lines.append(f'- {linux_name}')
    report_lines.extend([
        '',
        'Note: Unmapped programs may still be used on Windows via WSL, virtualization, or web alternatives.',
        'This report is a compatibility guideline, not an installer.',
    ])

    if output_dir:
        output_dir = Path(output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / output_name
        report_path.write_text('\n'.join(report_lines) + '\n', encoding='utf-8')
        print(f'Report written to {report_path}')
        return mapped, unmapped, report_path
    return mapped, unmapped, None


def generate_ninite_slugs(programs, mapping=None):
    if mapping is None:
        mapping = {}
    mapping = {str(k).strip().lower(): v for k, v in mapping.items()}

    slugs = []
    mapped = []
    unmapped = []
    for program in programs:
        key = program.strip().lower()
        if not key:
            continue
        slug = None
        if key in mapping:
            candidate = str(mapping[key]).strip().lower()
            slug = NINITE_APP_MAP.get(candidate)
            if slug is None:
                slug = NINITE_APP_MAP.get(key)
        else:
            slug = NINITE_APP_MAP.get(key)

        if slug:
            slugs.append(slug)
            mapped.append((program.strip(), slug))
        else:
            unmapped.append(program.strip())
    return sorted(set(slugs)), mapped, unmapped


def build_ninite_url(slugs):
    if not slugs:
        raise MigrationError('No Ninite-supported apps found for the provided Linux program list.')
    unique_slugs = sorted(set(slugs))
    slug_path = '-'.join(unique_slugs)
    return f'https://ninite.com/{slug_path}/'


def print_progress_bar(iteration, total, prefix='', suffix='', length=40):
    if total == 0:
        return
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()


def copy_paths(paths, destination, dry_run=False, show_progress=False):
    destination = Path(destination).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    path_list = normalize_paths(paths)
    total = len(path_list)
    for index, path in enumerate(path_list, start=1):
        if not path.exists():
            print(f"Skipping missing path: {path}")
            if show_progress:
                print_progress_bar(index, total, prefix='Copying paths:', suffix='Skipped', length=30)
            continue
        target = destination / path.name
        if dry_run:
            print(f"DRY RUN: would copy {path} -> {target}")
            copied.append(str(path))
            if show_progress:
                print_progress_bar(index, total, prefix='Copying paths:', suffix='Dry run', length=30)
            continue
        if path.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(path, target, symlinks=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        copied.append(str(path))
        if show_progress:
            print_progress_bar(index, total, prefix='Copying paths:', suffix='Done', length=30)
    if show_progress:
        print()
    return copied


def draw_menu(stdscr, options, selected):
    stdscr.clear()
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, -1)
        logo_style = curses.color_pair(1) | curses.A_BOLD
    else:
        logo_style = curses.A_BOLD
    for idx, line in enumerate(LOGO_LINES):
        stdscr.addstr(idx, 0, line, logo_style)
    stdscr.addstr(len(LOGO_LINES) + 1, 0, 'Select an action with ↑/↓ and Enter:', curses.A_BOLD)
    for idx, option in enumerate(options):
        style = curses.A_REVERSE if idx == selected else curses.A_NORMAL
        stdscr.addstr(len(LOGO_LINES) + 3 + idx, 2, option, style)
    stdscr.refresh()


def choose_action_text():
    options = [
        'export',
        'plan',
        'copy',
        'win2linux',
        'linux2win',
        'ninite',
        'deploy',
        'quit',
    ]
    print(ANSI_PINK + '\n'.join(LOGO_LINES) + ANSI_RESET)
    print('Select an action:')
    for idx, option in enumerate(options, start=1):
        print(f'  {idx}. {option}')
    while True:
        choice = input('Enter number: ').strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print('Invalid selection; try again.')


def choose_action():
    options = [
        'Export packages & files',
        'Generate install plan',
        'Copy selected files',
        'Windows to Linux migration',
        'Linux to Windows migration',
        'Generate Ninite installer URL',
        'Deploy manifest packages',
        'Quit',
    ]
    try:
        def _menu(stdscr):
            curses.curs_set(0)
            selected = 0
            while True:
                draw_menu(stdscr, options, selected)
                key = stdscr.getch()
                if key in (curses.KEY_UP, ord('k')):
                    selected = (selected - 1) % len(options)
                elif key in (curses.KEY_DOWN, ord('j')):
                    selected = (selected + 1) % len(options)
                elif key in (curses.KEY_ENTER, 10, 13):
                    return ['export', 'plan', 'copy', 'win2linux', 'linux2win', 'ninite', 'deploy', 'quit'][selected]
        return curses.wrapper(_menu)
    except curses.error:
        return choose_action_text()


def ask(prompt, default=None):
    full_prompt = f'{prompt} [{default}]' if default else prompt
    value = input(f'{full_prompt}: ').strip()
    return value or default


def ask_bool(prompt, default=False):
    default_text = 'Y/n' if default else 'y/N'
    value = input(f'{prompt} ({default_text}): ').strip().lower()
    if value == '':
        return default
    return value in ('y', 'yes')


def build_interactive_args(selection):
    if selection == 'export':
        source_distro = ask('Source distro (leave blank to auto-detect)', '')
        manifest = ask('Manifest file', 'migration-manifest.json')
        output_dir = ask('Output directory', 'migration-data')
        include_raw = ask('Paths to include (space-separated)', ' '.join(DEFAULT_FILES))
        dry_run = ask_bool('Dry run', False)
        args = ['export', '--manifest', manifest, '--output-dir', output_dir]
        if source_distro:
            args.extend(['--source-distro', source_distro])
        if dry_run:
            args.append('--dry-run')
        args.extend(['--include'] + include_raw.split())
        return args

    if selection == 'plan':
        manifest = ask('Manifest file', 'migration-manifest.json')
        target_distro = ask('Target distro', 'ubuntu')
        map_file = ask('Package map JSON file (leave blank for none)', '')
        output = ask('Output script', 'install-target.sh')
        args = ['plan', manifest, '--target-distro', target_distro, '--output', output]
        if map_file:
            args.extend(['--map', map_file])
        return args

    if selection == 'copy':
        paths_raw = ask('Paths to copy (space-separated)', ' '.join(DEFAULT_FILES))
        destination = ask('Destination folder', '/tmp/migration-bundle')
        dry_run = ask_bool('Dry run', False)
        args = ['copy', '--destination', destination]
        if dry_run:
            args.append('--dry-run')
        args.extend(['--paths'] + paths_raw.split())
        return args

    if selection == 'win2linux':
        target_distro = ask('Target distro', 'ubuntu')
        programs_file = ask('Windows programs file path (leave blank to enter manually)', '')
        output_dir = ask('Migration folder', 'migration-data')
        generate_report = ask_bool('Generate migration report', True)
        args = ['win2linux', '--target-distro', target_distro, '--output-dir', output_dir]
        if programs_file:
            args.extend(['--programs-file', programs_file])
        if generate_report:
            args.append('--generate-report')
        return args

    if selection == 'linux2win':
        target_platform = ask('Target platform', 'windows11')
        programs_file = ask('Linux programs file path (leave blank to enter manually)', '')
        output_dir = ask('Migration folder', 'migration-data')
        generate_report = ask_bool('Generate migration report', True)
        generate_ninite = ask_bool('Generate a Ninite bundle URL', False)
        ninite_output = ''
        if generate_ninite:
            ninite_output = ask('Save Ninite URL to file (leave blank to skip)', '')
        args = ['linux2win', '--target-platform', target_platform, '--output-dir', output_dir]
        if programs_file:
            args.extend(['--programs-file', programs_file])
        if generate_report:
            args.append('--generate-report')
        if generate_ninite:
            args.append('--ninite')
        if ninite_output:
            args.extend(['--ninite-output', ninite_output])
        return args

    if selection == 'ninite':
        programs_file = ask('Linux programs file path (leave blank to enter manually)', '')
        output_path = ask('Save Ninite URL to file (leave blank to skip)', '')
        map_file = ask('Package map JSON file (leave blank for none)', '')
        args = ['ninite']
        if programs_file:
            args.extend(['--programs-file', programs_file])
        if output_path:
            args.extend(['--output', output_path])
        if map_file:
            args.extend(['--map', map_file])
        return args

    if selection == 'deploy':
        manifest = ask('Manifest file', 'migration-manifest.json')
        target_distro = ask('Target distro', 'ubuntu')
        map_file = ask('Package map JSON file (leave blank for none)', '')
        save_script = ask('Save install script as', 'install-target.sh')
        dry_run = ask_bool('Dry run', False)
        force = ask_bool('Force deploy without confirmation', False)
        args = ['deploy', manifest, '--target-distro', target_distro, '--save-script', save_script]
        if map_file:
            args.extend(['--map', map_file])
        if dry_run:
            args.append('--dry-run')
        if force:
            args.append('--force')
        return args

    raise MigrationError('Unknown interactive selection.')


def main(cli_args=None):
    parser = argparse.ArgumentParser(
        description='Kiamira - Linux distro migration helper for packages and files.'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    export_parser = subparsers.add_parser('export', help='Export installed packages and selected files from the source system.')
    export_parser.add_argument('--source-distro', help='Source distro identifier to use instead of auto-detecting.')
    export_parser.add_argument('--manifest', default='migration-manifest.json', help='Output manifest file path.')
    export_parser.add_argument('--include', nargs='+', default=DEFAULT_FILES, help='Files and directories to include in the archive.')
    export_parser.add_argument('--include-home', action='store_true', help='Also copy the entire home directory into the migration bundle.')
    export_parser.add_argument('--output-dir', default='migration-data', help='Dir to copy selected files into.')
    export_parser.add_argument('--dry-run', action='store_true', help='Show what would be exported without copying files.')

    plan_parser = subparsers.add_parser('plan', help='Generate an install script for a target distro from a manifest.')
    plan_parser.add_argument('manifest', help='Input migration manifest file.')
    plan_parser.add_argument('--target-distro', required=True, help='Target distro identifier.')
    plan_parser.add_argument('--map', help='Optional JSON file with package name translations from source->target.')
    plan_parser.add_argument('--output', default='install-target.sh', help='Output install script filename.')

    win2linux_parser = subparsers.add_parser('win2linux', help='Assess Windows applications for migration to Linux.')
    win2linux_parser.add_argument('--target-distro', required=True, help='Target distro identifier for Linux.')
    win2linux_parser.add_argument('--programs-file', help='Text or JSON file containing Windows program names to assess.')
    win2linux_parser.add_argument('--output-dir', default='migration-data', help='Directory where the migration report will be written.')
    win2linux_parser.add_argument('--generate-report', action='store_true', help='Write a report file listing migrated and unmapped programs.')
    win2linux_parser.add_argument('--map', help='Optional JSON file with additional Windows->Linux program mappings.')

    linux2win_parser = subparsers.add_parser('linux2win', help='Assess Linux applications for migration to Windows.')
    linux2win_parser.add_argument('--target-platform', required=True, help='Target Windows platform identifier.')
    linux2win_parser.add_argument('--programs-file', help='Text or JSON file containing Linux program names to assess.')
    linux2win_parser.add_argument('--output-dir', default='migration-data', help='Directory where the migration report will be written.')
    linux2win_parser.add_argument('--generate-report', action='store_true', help='Write a report file listing migrated and unmapped programs.')
    linux2win_parser.add_argument('--ninite', action='store_true', help='Generate a Ninite installer URL for mapped Windows apps.')
    linux2win_parser.add_argument('--ninite-output', help='Save the generated Ninite URL to a file.')
    linux2win_parser.add_argument('--map', help='Optional JSON file with additional Linux->Windows program mappings.')

    ninite_parser = subparsers.add_parser('ninite', help='Generate a Ninite bundle URL from Linux applications.')
    ninite_parser.add_argument('--programs-file', help='Text or JSON file containing Linux program names to translate.')
    ninite_parser.add_argument('--output', help='Save the generated Ninite URL to a file.')
    ninite_parser.add_argument('--map', help='Optional JSON file with additional Linux->Ninite app mappings.')

    deploy_parser = subparsers.add_parser('deploy', help='Deploy the saved manifest package list to a target distro.')
    deploy_parser.add_argument('manifest', help='Migration manifest file.')
    deploy_parser.add_argument('--target-distro', required=True, help='Target distro identifier.')
    deploy_parser.add_argument('--map', help='Optional JSON file with package name translations from source->target.')
    deploy_parser.add_argument('--dry-run', action='store_true', help='Show install command without executing it.')
    deploy_parser.add_argument('--force', action='store_true', help='Bypass deploy confirmation prompt.')
    deploy_parser.add_argument('--save-script', help='Save the generated install script for review.')

    copy_parser = subparsers.add_parser('copy', help='Copy selected files into a destination package.')
    copy_parser.add_argument('--paths', nargs='+', default=DEFAULT_FILES, help='Paths to copy.')
    copy_parser.add_argument('--destination', required=True, help='Destination folder to store files.')
    copy_parser.add_argument('--dry-run', action='store_true', help='Show copy operations without executing them.')

    if cli_args is None:
        cli_args = sys.argv[1:]
    if not cli_args:
        selection = choose_action()
        if selection == 'quit':
            print('Quitting Kiamira. Goodbye!')
            sys.exit(0)
        cli_args = build_interactive_args(selection)
        print('Running: migrate.py ' + ' '.join(cli_args))

    args = parser.parse_args(cli_args)

    if args.command == 'export':
        source_platform = platform.system().lower()
        if source_platform == 'linux':
            source_distro = args.source_distro or detect_distro()
            print(f"Detected source distro: {source_distro}")
            installed_programs = scan_installed_programs(source_distro)
        elif source_platform == 'windows':
            source_distro = 'windows'
            print('Detected source platform: Windows')
            installed_programs = scan_installed_programs()
        else:
            source_distro = args.source_distro or detect_distro()
            print(f"Detected source platform: {source_platform}")
            installed_programs = scan_installed_programs(source_distro)

        print(f"Found {len(installed_programs)} installed programs.")
        packages = installed_programs
        files_to_copy = normalize_paths(args.include)
        if args.include_home:
            files_to_copy.append(Path.home())
        copied = []
        if not args.dry_run:
            copied = copy_paths([str(p) for p in files_to_copy], args.output_dir, dry_run=False, show_progress=True)
            print(f"Copied {len(copied)} paths into {args.output_dir}")
        else:
            copied = [str(p) for p in files_to_copy if p.exists()]
            for p in files_to_copy:
                print(f"DRY RUN: would copy {p}")

        manifest = {
            'source_platform': source_platform,
            'source_distro': source_distro,
            'installed_programs': installed_programs,
            'packages': packages,
            'copied_paths': copied,
            'files_destination': str(Path(args.output_dir).resolve()),
        }
        save_json_file(manifest, args.manifest)
        print(f"Migration manifest written to {args.manifest}")

    elif args.command == 'plan':
        manifest = load_json_file(args.manifest)
        packages = manifest.get('packages', [])
        mapping = {}
        if args.map:
            mapping = load_json_file(args.map)
            print(f"Loaded mapping for {len(mapping)} package entries.")
        script = build_install_script(packages, args.target_distro, mapping=mapping, output_path=args.output, show_progress=True)
        print(f"Install script written to {args.output}")
        print('---')
        print(script)
    elif args.command == 'win2linux':
        if args.programs_file:
            programs = load_program_list(args.programs_file)
        else:
            programs = ask_multiline('Enter Windows program names to assess:')
        mapping = {}
        if args.map:
            mapping = load_json_file(args.map)
        mapped, unmapped, report_path = build_windows_migration_report(
            programs,
            args.target_distro,
            mapping=mapping,
            output_dir=args.output_dir if args.generate_report else None,
        )
        print(f"Programs with Linux equivalents: {len(mapped)}")
        print(f"Programs without known equivalents: {len(unmapped)}")
        if args.generate_report and report_path:
            print(f"Migration report saved to: {report_path}")
    elif args.command == 'linux2win':
        if args.programs_file:
            programs = load_program_list(args.programs_file)
        else:
            programs = ask_multiline('Enter Linux program names to assess:')
        mapping = {}
        if args.map:
            mapping = load_json_file(args.map)
        mapped, unmapped, report_path = build_linux_migration_report(
            programs,
            args.target_platform,
            mapping=mapping,
            output_dir=args.output_dir if args.generate_report else None,
        )
        print(f"Programs with Windows equivalents: {len(mapped)}")
        print(f"Programs without known equivalents: {len(unmapped)}")
        if args.generate_report and report_path:
            print(f"Migration report saved to: {report_path}")
        if args.ninite:
            slugs, ninite_mapped, ninite_unmapped = generate_ninite_slugs(programs, mapping=mapping)
            try:
                ninite_url = build_ninite_url(slugs)
                print('Ninite installer URL:')
                print(ninite_url)
                if args.ninite_output:
                    output_path = Path(args.ninite_output).expanduser().resolve()
                    output_path.write_text(ninite_url + '\n', encoding='utf-8')
                    print(f'Ninite URL saved to {output_path}')
            except MigrationError as exc:
                print(f'Warning: {exc}')
            if ninite_mapped:
                print(f'Ninite-supported apps found: {len(ninite_mapped)}')
            if ninite_unmapped:
                print(f'Programs without Ninite support: {len(ninite_unmapped)}')
    elif args.command == 'ninite':
        if args.programs_file:
            programs = load_program_list(args.programs_file)
        else:
            programs = ask_multiline('Enter Linux program names to translate:')
        mapping = {}
        if args.map:
            mapping = load_json_file(args.map)
        slugs, ninite_mapped, ninite_unmapped = generate_ninite_slugs(programs, mapping=mapping)
        ninite_url = build_ninite_url(slugs)
        print('Ninite installer URL:')
        print(ninite_url)
        if args.output:
            output_path = Path(args.output).expanduser().resolve()
            output_path.write_text(ninite_url + '\n', encoding='utf-8')
            print(f'Ninite URL saved to {output_path}')
        print(f'Ninite-supported apps found: {len(ninite_mapped)}')
        if ninite_unmapped:
            print(f'Programs without Ninite support: {len(ninite_unmapped)}')
    elif args.command == 'deploy':
        mapping = {}
        if args.map:
            mapping = load_json_file(args.map)
        translated, install_cmd = deploy_manifest(
            args.manifest,
            args.target_distro,
            mapping=mapping,
            dry_run=args.dry_run,
            save_script=args.save_script,
            force=args.force,
        )
        print(f"Deploy candidate package count: {len(translated)}")
    elif args.command == 'copy':
        copied = copy_paths(args.paths, args.destination, dry_run=args.dry_run, show_progress=True)
        if not args.dry_run:
            print(f"Copied {len(copied)} path(s) into {args.destination}")
        else:
            print(f"DRY RUN: {len(copied)} path(s) would be copied.")


if __name__ == '__main__':
    try:
        main()
    except MigrationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
