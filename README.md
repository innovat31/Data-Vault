# Data Vault

A Windows desktop application and CLI for local file storage and version history.
All application-managed file reads and writes are restricted to **D:**. No network
services, third-party Python dependencies, account, or installation are required.

## Start

From PowerShell in this project folder:

```powershell
.\launch.ps1
```

The launcher uses the self-contained Python runtime already present at
`D:\setup\Wallpaper Engine\dlc\pymidas\python.exe`. It runs in isolated mode,
disables site initialization and bytecode generation, and sets temporary/cache
locations under this project's `.runtime` folder. It restores the calling shell's
environment afterward. It does not use the existing virtual environments, which
depend on a C: installation. No packages are installed or runtime files modified.

For another full Python installation **on D:** (Python 3.9+ with Tk 8.6 for the GUI):

```powershell
.\launch.ps1 -PythonExe 'D:\Tools\Python\python.exe'
```

If script execution is disabled, run it for this process only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\launch.ps1
```

## Desktop workflow

The desktop uses a soft mint, lavender, and peach palette, live storage summary
cards, and clear collection/history panels. Gentle motion includes drifting
banner artwork, smooth button hovers, and sliding completion messages. Turn off
**Gentle motion** in the header for a still interface. No extra packages or
downloaded assets are needed.

1. **Import file** opens a browser limited to D:. Double-click folders or enter a
   D: folder in the address bar. Pick a file, then Open.
2. Importing the same filename creates another version. Names are case-insensitive,
   as on Windows. Files with the same basename in different folders share history.
3. Select a file to see its versions, sizes, timestamps, and checksums. Search by
   filename using the field above the file list.
4. **Use selected version** changes which version is current, preserving history.
   **Export current** writes that version to a chosen D: folder. Replacing an
   existing destination requires confirmation.
5. **Verify all versions** detects missing or altered content. **Delete file**
   removes every version after confirmation.

File operations run in a worker thread. Wait for them to finish before closing.
Only one application or CLI process may open a given vault at a time.

## CLI

```powershell
.\launch.ps1 list
.\launch.ps1 add 'D:\Documents\report.pdf'
.\launch.ps1 history 'report.pdf'
.\launch.ps1 rollback 'report.pdf' 1
.\launch.ps1 export 'report.pdf' 'D:\Documents\report-restored.pdf'
.\launch.ps1 verify
.\launch.ps1 delete 'report.pdf' --yes
.\launch.ps1 --vault 'D:\MyVault' list
```

Use `--help` for commands and `export --help` for overwrite options. CLI errors
return a nonzero exit status. Direct `data_vault.py` execution is also supported,
but use the launcher to control interpreter startup and temporary paths.

## Storage and reliability

Default storage is `data_vault` **beside this project's code**, regardless of the
current working directory. Metadata lives in `metadata.json`, and each copy is in
`files/<name>/v<number>/<name>`. Sources remain unchanged. New versions use full
SHA-256 checksums; the original application's 16-character checksums remain
readable. Legacy timestamps retain their original local time; new ones are UTC.

Metadata is validated and atomically replaced after file content is flushed to
disk. Failed saves preserve the last committed metadata. Interrupted imports may
leave unindexed version folders; future imports skip them instead of overwriting
their contents. Deletion stages content in `.deleted-<id>` before updating the
index; a power loss between these steps can require manual recovery. Retain a
separate backup of the whole vault for power loss or disk failure recovery. Close
the application before copying or restoring its folder.

Invalid metadata is reported instead of reset. Do not remove `metadata.json` to
fix an error: preserve the vault and restore a known-good backup. Failed deletion
cleanup reports the retained folder so it can be reviewed.

Paths on other drives, UNC/network paths, device paths, alternate data streams,
parent traversal, symbolic links, junctions, and other reparse points are rejected
before the application follows them. The custom file browser does not invoke the
Windows file dialog or browse C:. Exporting into the vault itself is prohibited.

This is a local version store: **files are not encrypted or password-protected**.
Checksums detect accidental changes; they do not authenticate against someone who
can rewrite both files and metadata. Path checks are application controls, not an
OS sandbox against another process concurrently replacing directories. Windows,
PowerShell, and Python may load operating-system libraries or fonts from the
system drive; application data, selected files, temp files, and caches stay on D:.

## Tests

```powershell
.\test.ps1
```

Tests use only generated data in `.runtime/tests` on D:, exercise actual Windows
paths and file locks, and use the same isolated D: interpreter. No existing user
files are changed. Packaging entry points are defined in `pyproject.toml`; normal
use requires no build or package installation.
