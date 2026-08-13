Set-StrictMode -Version latest

$ScriptDirectory = Split-Path -parent $PSCommandPath
& "$ScriptDirectory/emsdk.ps1" construct_env
