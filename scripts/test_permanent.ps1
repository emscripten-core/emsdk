$repo_root = [System.IO.Path]::GetDirectoryName((resolve-path "$PSScriptRoot"))

& "$repo_root/emsdk.ps1" install latest
& "$repo_root/emsdk.ps1" activate latest --permanent

$EMSDK_USER = [System.Environment]::GetEnvironmentVariable("EMSDK", "User")
$EM_CONFIG_USER = [System.Environment]::GetEnvironmentVariable("EM_CONFIG", "User")
$EMSDK_NODE_USER = [System.Environment]::GetEnvironmentVariable("EMSDK_NODE", "User")
$EMSDK_PYTHON_USER = [System.Environment]::GetEnvironmentVariable("EMSDK_PYTHON", "User")
$JAVA_HOME_USER = [System.Environment]::GetEnvironmentVariable("JAVA_HOME", "User")
$EM_CACHE_USER = [System.Environment]::GetEnvironmentVariable("EM_CACHE", "User")
$PATH_USER = [System.Environment]::GetEnvironmentVariable("PATH", "User")

if (!$EMSDK_USER) {
    throw "EMSDK is not set for the user"
}
if (!$EM_CONFIG_USER) {
    throw "EM_CONFIG_USER is not set for the user"
}
if (!$EMSDK_NODE_USER) {
    throw "EMSDK_NODE is not set for the user"
}
if (!$JAVA_HOME_USER) {
    throw "JAVA_HOME is not set for the user"
}
if (!$EMSDK_PYTHON_USER) {
    throw "EMSDK_PYTHON is not set for the user"
}
if (!$EM_CACHE_USER) {
    throw "EM_CACHE is not set for the user"
}


$path_split = $PATH_USER.Split(';')

$EMSDK_Path_USER = $path_split | Where-Object { $_ -match 'emsdk' }
if (!$EMSDK_Path_USER) {
    throw "No path is added!"
}
$EMSDK_NODE_Path_USER = $path_split | Where-Object { $_ -match 'emsdk\\node' }
if (!$EMSDK_NODE_Path_USER) {
    throw "emsdk\node is not added to path."
}
$EMSDK_PYTHON_Path_USER = $path_split | Where-Object { $_ -match 'emsdk\\python' }
if (!$EMSDK_PYTHON_Path_USER) {
    throw "emsdk\python is not added to path."
}
$EMSDK_JAVA_Path_USER = $path_split | Where-Object { $_ -match 'emsdk\\java' }
if (!$EMSDK_JAVA_Path_USER) {
    throw "emsdk\java is not added to path."
}

$EMSDK_UPSTREAM_Path_USER = $path_split | Where-Object { $_ -match 'emsdk\\upstream\\emscripten' }
if (!$EMSDK_UPSTREAM_Path_USER) {
    throw "emsdk\upstream\emscripten is not added to path."
}
