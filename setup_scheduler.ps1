# ==============================================================================
# Script cài đặt Windows Task Scheduler cho VNStock Mini SWE Agent
# Tự động chạy vào 17:00 mỗi ngày từ Thứ Hai đến Thứ Sáu
# ==============================================================================
param (
    [string]$BarkKey = "",
    [string]$GeminiApiKey = "AQ.Ab8RN6JYLtPpgz2C9hT4MeF3Rx1n0y6LsHz9sgUcMDQGguUFKg",
    [string]$Watchlist = "",
    [string]$Symbols = "VNINDEX,VN30,VN100",
    [switch]$Uninstall,
    [switch]$RunNow
)

$TaskName = "VNStock-Daily-Agent"
$CurrentDir = $PSScriptRoot
$PythonExe = (Get-Command python).Source

if (-not $PythonExe) {
    Write-Error "Không tìm thấy python trong PATH hệ thống. Vui lòng kiểm tra lại!"
    exit 1
}

# 1. Gỡ cài đặt nếu có cờ -Uninstall
if ($Uninstall) {
    Write-Host "🗑️ Đang gỡ bỏ tác vụ $TaskName khỏi Windows Task Scheduler..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ Đã gỡ bỏ thành công tác vụ $TaskName!" -ForegroundColor Green
    exit 0
}

# 2. Xây dựng tham số dòng lệnh cho main.py
$ScriptPath = Join-Path $CurrentDir "main.py"
$ArgList = "`"$ScriptPath`""

if ($Symbols) {
    $ArgList += " --symbols `"$Symbols`""
}
if ($Watchlist) {
    $ArgList += " --watchlist `"$Watchlist`""
}
if ($BarkKey) {
    $ArgList += " --bark-key `"$BarkKey`""
}
if ($GeminiApiKey) {
    $ArgList += " --gemini-api-key `"$GeminiApiKey`""
}

# 3. Tạo Task Action và Trigger
Write-Host "⚙️ Đang cấu hình tác vụ Windows Task Scheduler: $TaskName" -ForegroundColor Cyan
Write-Host "• Python executable: $PythonExe"
Write-Host "• Script path: $ScriptPath"
Write-Host "• Lịch chạy: 17:00 các ngày Thứ 2, 3, 4, 5, 6 hàng tuần"

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ArgList -WorkingDirectory $CurrentDir
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 5:00PM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 4. Đăng ký tác vụ vào hệ thống
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Tự động phân tích thị trường chứng khoán VN và bắn thông báo qua Bark lúc 17:00" -Force | Out-Null

Write-Host "✅ ĐÃ ĐĂNG KÝ THÀNH CÔNG TÁC VỤ [$TaskName]!" -ForegroundColor Green
Write-Host "Tác vụ sẽ tự động kích hoạt vào lúc 17:00 từ Thứ 2 đến Thứ 6." -ForegroundColor Green
Write-Host ""
Write-Host "💡 Các lệnh hữu ích:"
Write-Host "   - Chạy thử ngay lập tức: Start-ScheduledTask -TaskName `"$TaskName`""
Write-Host "   - Gỡ bỏ lịch: .\setup_scheduler.ps1 -Uninstall"

if ($RunNow) {
    Write-Host "`n🚀 Đang kích hoạt chạy thử ngay..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
}

