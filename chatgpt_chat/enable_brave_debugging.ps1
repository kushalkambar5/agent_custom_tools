$sh = New-Object -ComObject WScript.Shell

# 1. Update Taskbar shortcut
$taskbarLnk = "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\Brave.lnk"
if (Test-Path $taskbarLnk) {
    $s = $sh.CreateShortcut($taskbarLnk)
    if ($s.Arguments -notmatch "--remote-debugging-port=9222") {
        $s.Arguments = "--remote-debugging-port=9222 " + $s.Arguments
        $s.Save()
        Write-Host "Updated Taskbar Brave shortcut with remote debugging."
    } else {
        Write-Host "Taskbar Brave shortcut already has remote debugging enabled."
    }
}

# 2. Update or Create Desktop shortcut
$desktopPath = [Environment]::GetFolderPath('Desktop')
$desktopLnk = Join-Path $desktopPath "Brave.lnk"
$braveExe = "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
if (Test-Path $braveExe) {
    $ds = $sh.CreateShortcut($desktopLnk)
    $ds.TargetPath = $braveExe
    $ds.Arguments = "--remote-debugging-port=9222"
    $ds.WorkingDirectory = "C:\Program Files\BraveSoftware\Brave-Browser\Application"
    $ds.Save()
    Write-Host "Created/Updated Desktop Brave shortcut with remote debugging: $desktopLnk"
}
