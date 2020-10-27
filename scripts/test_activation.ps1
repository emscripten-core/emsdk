# This test installs emsdk and activates the latest toolchain using `--system` or `--permanent` flags, and checks if the environment variables and PATH are correctly updated. Set $env:SYSTEM_FLAG and $env:PERMANENT_FLAG to test each. If no flag is provided the process/shell values are tested. See the CI file for an example.

refreshenv

$repo_root = [System.IO.Path]::GetDirectoryName((resolve-path "$PSScriptRoot"))

$PATH_USER_BEFORE = [System.Environment]::GetEnvironmentVariable("PATH", "User")
$PATH_MACHINE_BEFORE = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
$PATH_Process_BEFORE = [System.Environment]::GetEnvironmentVariable("PATH", "Process")


try {

    & "$repo_root/emsdk.ps1" install latest

    $esc = '--%'
    & "$repo_root/emsdk.ps1" activate latest $esc $env:PERMANENT_FLAG $env:SYSTEM_FLAG

    if ($env:SYSTEM_FLAG) {
        $env_type = "Machine"
    }
    elseif ($env:PERMANENT_FLAG) {
        $env_type = "User"
    } else {
        $env_type = "Process"
    }

    $EMSDK = [System.Environment]::GetEnvironmentVariable("EMSDK", $env_type)
    $EM_CONFIG = [System.Environment]::GetEnvironmentVariable("EM_CONFIG", $env_type)
    $EMSDK_NODE = [System.Environment]::GetEnvironmentVariable("EMSDK_NODE", $env_type)
    $EMSDK_PYTHON = [System.Environment]::GetEnvironmentVariable("EMSDK_PYTHON", $env_type)
    $JAVA_HOME = [System.Environment]::GetEnvironmentVariable("JAVA_HOME", $env_type)
    $EM_CACHE = [System.Environment]::GetEnvironmentVariable("EM_CACHE", $env_type)
    $PATH = [System.Environment]::GetEnvironmentVariable("PATH", $env_type)

    if (!$EMSDK) {
        throw "EMSDK is not set for the user"
    }
    if (!$EM_CONFIG) {
        throw "EM_CONFIG is not set for the user"
    }
    if (!$EMSDK_NODE) {
        throw "EMSDK_NODE is not set for the user"
    }
    if (!$JAVA_HOME) {
        throw "JAVA_HOME is not set for the user"
    }
    if (!$EMSDK_PYTHON) {
        throw "EMSDK_PYTHON is not set for the user"
    }
    if (!$EM_CACHE) {
        throw "EM_CACHE is not set for the user"
    }


    $path_split = $PATH.Split(';')

    $EMSDK_Path = $path_split | Where-Object { $_ -like "$repo_root*" }
    if (!$EMSDK_Path) {
        throw "No path is added!"
    }
    $EMSDK_NODE_Path = $path_split | Where-Object { $_ -like "$repo_root\node*" }
    if (!$EMSDK_NODE_Path) {
        throw "$repo_root\\node is not added to path."
    }
    $EMSDK_PYTHON_Path = $path_split | Where-Object { $_ -like "$repo_root\python*" }
    if (!$EMSDK_PYTHON_Path) {
        throw "$repo_root\\python is not added to path."
    }
    $EMSDK_JAVA_Path = $path_split | Where-Object { $_ -like "$repo_root\java*" }
    if (!$EMSDK_JAVA_Path) {
        throw "$repo_root\\java is not added to path."
    }

    $EMSDK_UPSTREAM_Path = $path_split | Where-Object { $_ -like "$repo_root\upstream\emscripten*" }
    if (!$EMSDK_UPSTREAM_Path) {
        throw "$repo_root\\upstream\emscripten is not added to path."
    }


}
finally {
    # Recover pre-split PATH
    refreshenv

    [Environment]::SetEnvironmentVariable("Path", $PATH_USER_BEFORE, "User")
    try {
        [Environment]::SetEnvironmentVariable("Path", $PATH_MACHINE_BEFORE, "Machine")
    }
    catch {}

    [Environment]::SetEnvironmentVariable("Path", $PATH_Process_BEFORE, "Process")

    refreshenv

}
