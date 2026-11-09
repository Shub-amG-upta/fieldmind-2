# Keeps the QIDK attached to WSL whatever port number it comes back on. Stops on its own after 30 hours.
$u = "C:\Program Files\usbipd-win\usbipd.exe"
$end = (Get-Date).AddHours(30)
$last = ""
while ((Get-Date) -lt $end) {
    $line = & $u list 2>$null | Select-String "05c6:901d" | Select-Object -First 1
    if ($line) {
        $text = $line.ToString()
        $bus = ($text -split "\s+")[0]
        if ($text -notmatch "Attached") {
            if ($text -match "Not shared") {
                if ($last -ne "unshared $bus") { "$(Get-Date -Format s) $bus is not shared: needs an admin 'usbipd bind'"; $last = "unshared $bus" }
            } else {
                $r = & $u attach --wsl --busid $bus 2>&1 | Select-Object -Last 1
                "$(Get-Date -Format s) attach $bus : $r"
                $last = "attach $bus"
            }
        }
    }
    Start-Sleep -Seconds 4
}
