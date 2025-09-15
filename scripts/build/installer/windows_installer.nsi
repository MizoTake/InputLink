; Input Link Windows Installer Script
; Created with NSIS (Nullsoft Scriptable Install System)

!define APP_NAME "Input Link"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Input Link Team"
!define APP_URL "https://github.com/inputlink/inputlink"
!define APP_DESCRIPTION "Network Controller Forwarding System"

; Installer settings
Name "${APP_NAME}"
OutFile "InputLink-${APP_VERSION}-Windows-Installer.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

; Interface settings
!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Version Information
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "Comments" "${APP_DESCRIPTION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "LegalTrademarks" ""
VIAddVersionKey "LegalCopyright" "© ${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"

Section "Input Link Core" SecCore
  SectionIn RO  ; Read-only section
  
  SetOutPath $INSTDIR
  
  ; Copy executable files
  File "..\..\dist\InputLink-Sender.exe"
  File "..\..\dist\InputLink-Receiver.exe"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\Input Link Sender.lnk" "$INSTDIR\InputLink-Sender.exe"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\Input Link Receiver.lnk" "$INSTDIR\InputLink-Receiver.exe"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  ; Create Desktop shortcuts (optional)
  CreateShortCut "$DESKTOP\Input Link Sender.lnk" "$INSTDIR\InputLink-Sender.exe"
  CreateShortCut "$DESKTOP\Input Link Receiver.lnk" "$INSTDIR\InputLink-Receiver.exe"
  
  ; Write registry keys
  WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "ViGEm Bus Driver" SecViGEm
  DetailPrint "Checking for ViGEm Bus Driver..."
  
  ; Check if ViGEm is already installed
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{9F69CC95-0E80-46FD-9E58-FC0B47CC85C1}" "DisplayName"
  StrCmp $0 "" 0 ViGEmExists
  
  DetailPrint "ViGEm Bus Driver not found. Installation required for Windows virtual controller support."
  MessageBox MB_YESNO|MB_ICONQUESTION "Input Link requires the ViGEm Bus Driver for virtual controller support.$\r$\n$\r$\nWould you like to download and install it now?" IDYES DownloadViGEm IDNO SkipViGEm
  
  DownloadViGEm:
    DetailPrint "Downloading ViGEm Bus Driver..."
    NSISdl::download "https://github.com/ViGEm/ViGEmBus/releases/latest/download/ViGEmBus_Setup_x64.exe" "$TEMP\ViGEmBus_Setup.exe"
    Pop $0
    StrCmp $0 "success" 0 DownloadFailed
    
    DetailPrint "Installing ViGEm Bus Driver..."
    ExecWait '"$TEMP\ViGEmBus_Setup.exe" /S' $0
    StrCmp $0 "0" ViGEmInstalled ViGEmFailed
    
    ViGEmInstalled:
      DetailPrint "ViGEm Bus Driver installed successfully."
      Delete "$TEMP\ViGEmBus_Setup.exe"
      Goto ViGEmDone
    
    ViGEmFailed:
      MessageBox MB_OK|MB_ICONEXCLAMATION "ViGEm Bus Driver installation failed. You may need to install it manually."
      Delete "$TEMP\ViGEmBus_Setup.exe"
      Goto ViGEmDone
    
    DownloadFailed:
      MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to download ViGEm Bus Driver. Please install manually from: https://vigembusdriver.com"
      Goto ViGEmDone
  
  SkipViGEm:
    DetailPrint "Skipped ViGEm Bus Driver installation."
    Goto ViGEmDone
  
  ViGEmExists:
    DetailPrint "ViGEm Bus Driver already installed."
  
  ViGEmDone:
SectionEnd

Section "Documentation" SecDocs
  SetOutPath $INSTDIR
  File "..\..\README.md"
  File "..\..\LICENSE"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core Input Link applications (Sender and Receiver)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecViGEm} "ViGEm Bus Driver for virtual controller support on Windows"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "Documentation and license files"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  DeleteRegKey HKLM "SOFTWARE\${APP_NAME}"
  
  ; Remove files and directories
  Delete "$INSTDIR\InputLink-Sender.exe"
  Delete "$INSTDIR\InputLink-Receiver.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\uninstall.exe"
  
  ; Remove shortcuts
  Delete "$SMPROGRAMS\${APP_NAME}\*.*"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  Delete "$DESKTOP\Input Link Sender.lnk"
  Delete "$DESKTOP\Input Link Receiver.lnk"
  
  ; Remove installation directory
  RMDir "$INSTDIR"
SectionEnd