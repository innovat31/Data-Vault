# All application paths and temporary files remain on D:. No installation required.
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$PythonExe = 'D:\setup\Wallpaper Engine\dlc\pymidas\python.exe',
    [switch]$RunTests,
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$VaultArguments
)
$ErrorActionPreference = 'Stop'

function Assert-DPath([string]$Value) {
    if (-not [IO.Path]::IsPathRooted($Value) -or $Value -notmatch '^D:[\\/]') {
        throw 'The project and Python runtime must use absolute paths on D:.'
    }
    $checkedPath = [IO.Path]::GetFullPath($Value)
    $ancestor = [IO.Path]::GetPathRoot($checkedPath)
    $parts = @('') + $checkedPath.Substring($ancestor.Length).Split([char]'\')
    foreach ($part in $parts) {
        if ($part) { $ancestor = Join-Path $ancestor $part }
        try {
            $item = Get-Item -LiteralPath $ancestor -Force -ErrorAction Stop
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Redirected paths are not allowed: $ancestor"
            }
        }
        catch [System.Management.Automation.ItemNotFoundException] { }
    }
    return $checkedPath
}

$projectPath = Assert-DPath $PSScriptRoot
$pythonPath = Assert-DPath $PythonExe
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw 'Python was not found on D:. Pass -PythonExe with a self-contained D: Python installation.'
}
$pythonDirectory = Split-Path -Parent $pythonPath
$pythonParent = Split-Path -Parent $pythonDirectory
if ((Test-Path -LiteralPath (Join-Path $pythonDirectory 'pyvenv.cfg')) -or
    (Test-Path -LiteralPath (Join-Path $pythonParent 'pyvenv.cfg'))) {
    throw 'Use a full D: Python installation, not a virtual environment that could depend on C:.'
}
foreach ($directory in @('Lib', 'DLLs', 'tcl')) {
    $null = Assert-DPath (Join-Path $pythonDirectory $directory)
}
$tempPath = Assert-DPath (Join-Path $projectPath '.runtime\tmp')
$cachePath = Assert-DPath (Join-Path $projectPath '.runtime\cache')
New-Item -ItemType Directory -Path $tempPath, $cachePath -Force | Out-Null

$envNames = @('TEMP', 'TMP', 'TMPDIR', 'PYTHONHOME', 'PYTHONPATH', 'PYTHONDONTWRITEBYTECODE',
    'XDG_CACHE_HOME', 'PIP_CACHE_DIR', 'TCL_LIBRARY', 'TK_LIBRARY')
$oldEnvironment = @{}
foreach ($name in $envNames) { $oldEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
$oldLocation = Get-Location
try {
    $env:TEMP = $tempPath
    $env:TMP = $tempPath
    $env:TMPDIR = $tempPath
    $env:PYTHONHOME = $pythonDirectory
    $env:PYTHONPATH = ''
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:XDG_CACHE_HOME = $cachePath
    $env:PIP_CACHE_DIR = $cachePath
    $env:TCL_LIBRARY = Join-Path $pythonDirectory 'tcl\tcl8.6'
    $env:TK_LIBRARY = Join-Path $pythonDirectory 'tcl\tk8.6'
    Set-Location -LiteralPath $projectPath
    $bootstrap = @'
import sys
if any(p and not p.replace('/', '\\').lower().startswith('d:\\') for p in sys.path):
    raise SystemExit('Python runtime search paths must stay on D:.')
project = sys.argv.pop(1)
mode = sys.argv.pop(1)
sys.path.insert(0, project)
if mode == 'test':
    from vault_app.paths import configure_runtime
    configure_runtime()
    import unittest
    suite = unittest.defaultTestLoader.discover(project + '/tests')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
from vault_app.cli import main
raise SystemExit(main())
'@
    $runMode = if ($RunTests) { 'test' } else { 'app' }
    & $pythonPath -I -S -B -c $bootstrap $projectPath $runMode @VaultArguments
    $vaultExitCode = $LASTEXITCODE
}
finally {
    Set-Location -LiteralPath $oldLocation.Path
    foreach ($name in $envNames) { [Environment]::SetEnvironmentVariable($name, $oldEnvironment[$name], 'Process') }
}
exit $vaultExitCode
