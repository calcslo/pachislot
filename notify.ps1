[CmdletBinding()]
param (
    [string]$Title = "P's Cube Server Error",
    [string]$Message = "サーバーが予期せぬエラーで停止しました。"
)

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$Template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
$Xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($Template)
$Xml.GetElementsByTagName("text")[0].AppendChild($Xml.CreateTextNode($Title)) | Out-Null
$Xml.GetElementsByTagName("text")[1].AppendChild($Xml.CreateTextNode($Message)) | Out-Null
$Toast = [Windows.UI.Notifications.ToastNotification]::new($Xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Pachislot Server").Show($Toast)
