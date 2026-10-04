# Data Vault

Data Vault is a Windows desktop app and command-line tool for keeping local file
versions. It stores copies on the D: drive, leaves source files unchanged, and
lets you inspect, restore, export, and verify stored versions.

## Requirements

- Windows and PowerShell
- A full Python 3.9+ installation on D:
- Tk 8.6 for the desktop app

The launcher defaults to
`D:\setup\Wallpaper Engine\dlc\pymidas\python.exe`. If your Python installation
is elsewhere on D:, pass its path with `-PythonExe`. Data Vault uses only the
Python standard library; no package installation is required.

## Run

Open PowerShell in the project folder and start the desktop app:

```powershell
.\launch.ps1
```

To use a different Python installation:

```powershell
.\launch.ps1 -PythonExe 'D:\Tools\Python\python.exe'
```

If PowerShell blocks the script, run it with a process-scoped execution-policy
override:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\launch.ps1
```

## Use the desktop app

- Import a file using the built-in browser, which can browse D: only.
- Files with the same name (case-insensitively) share a version history.
- Select a file to view its versions, sizes, timestamps, and checksums.
- Make an earlier version current, or export the current version to D:.
- Verify stored contents or delete a file and all its versions.

The app performs file operations in a worker thread. Only one app or CLI process
can open a vault at a time.

## Command line

Run commands through the launcher:

```powershell
.\launch.ps1 list
.\launch.ps1 add 'D:\Documents\report.pdf'
.\launch.ps1 history 'report.pdf'
.\launch.ps1 rollback 'report.pdf' 1
.\launch.ps1 export 'report.pdf' 'D:\Documents\report-restored.pdf'
.\launch.ps1 verify
.\launch.ps1 delete 'report.pdf' --yes
```

Use `--vault 'D:\MyVault'` before the command to select another vault. Export
does not overwrite an existing destination unless `--overwrite` is provided.
Deletion requires `--yes`. Run `.\launch.ps1 --help` or add `--help` to a
command for its options.

## Storage and safety

By default, the vault is the `data_vault` folder beside the project files.
Metadata is stored in `metadata.json`; version contents are under `files`.
Imports receive SHA-256 checksums, and verification checks stored contents
against their recorded sizes and checksums. Metadata updates are validated and
written atomically.

The launcher and application restrict managed files, the vault, and temporary
and cache files to D:. Paths on other drives, network paths, and redirected
paths such as symbolic links and junctions are rejected. These checks are
application safeguards, not an operating-system security boundary.

Files are not encrypted or password-protected. Keep a separate backup of the
entire vault; checksums detect accidental changes but do not prevent deliberate
tampering.

## Tests

Run the test suite from PowerShell:

```powershell
.\test.ps1
```

The tests use generated data under `.runtime\tests` on D:.
