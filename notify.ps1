[CmdletBinding()]
param (
    [string]$Title = "Server Error",
    [int]$ErrorCode = 0
)

$Message = "Pachislot server stopped."
if ($ErrorCode -ne 0) {
    $Message = "Server stopped with error code: $ErrorCode. Check if the port is already in use."
}

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$Template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
$Xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($Template)

$TextNodes = $Xml.GetElementsByTagName("text")
if ($TextNodes.Count -ge 1) {
    $TextNodes.Item(0).InnerText = $Title
}
if ($TextNodes.Count -ge 2) {
    $TextNodes.Item(1).InnerText = $Message
}

$Toast = [Windows.UI.Notifications.ToastNotification]::new($Xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Pachislot Server").Show($Toast)
