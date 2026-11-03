# Starts the game, captures its window, closes it. The capture reads the screen, so the window stays on top for a moment.
# Usage: efpse_shot.ps1 -Dir <Projects> -Project <name> -Out shot.png -Wait 8 [-Map 0] [-Shots 3] [-Gap 1] [-Keys "W:200,LMB:40,RMB:80,WAIT:500,SHOT"]
param([string]$Dir, [string]$Out, [int]$Wait = 2, [int]$Map = 0, [string]$Project, [string]$Keys = '', [int]$Shots = 0, [double]$Gap = 1, [string]$Clip = '', [int]$ClipSec = 0)
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices; using System.Threading;
public class Win {
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, Rt, B; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, IntPtr extra);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, IntPtr extra);
  public static void Hold(byte vk, int ms) { byte sc = (byte)MapVirtualKey(vk, 0); keybd_event(vk, sc, 0, IntPtr.Zero); Thread.Sleep(ms); keybd_event(vk, sc, 2, IntPtr.Zero); }
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint c, uint t);
  public static void Click(int ms) { mouse_event(2, 0, 0, 0, IntPtr.Zero); Thread.Sleep(ms); mouse_event(4, 0, 0, 0, IntPtr.Zero); }
  public static void Turn(int dx, int dy) { mouse_event(1, dx, dy, 0, IntPtr.Zero); }
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  public static bool Focus(IntPtr h) { if (GetForegroundWindow() == h) return true; keybd_event(0x12, 0, 0, IntPtr.Zero); SetForegroundWindow(h); keybd_event(0x12, 0, 2, IntPtr.Zero); Thread.Sleep(120); return GetForegroundWindow() == h; }
}
'@
[void][Win]::SetProcessDPIAware()
$dir = $Dir
$outDir = Split-Path $Out
$Out = Split-Path $Out -Leaf
New-Item -ItemType Directory -Force $outDir | Out-Null
$p = Start-Process -FilePath "$dir\Game.exe" -ArgumentList "-data $Project -map $Map -console" -WorkingDirectory $dir -PassThru
function Shot($name) {
  $r = New-Object Win+R; [void][Win]::GetWindowRect($p.MainWindowHandle, [ref]$r)
  $x = $r.L + 8; $y = $r.T + 31; $w = $r.Rt - $r.L - 16; $h = $r.B - $r.T - 39
  $b = New-Object Drawing.Bitmap $w, $h
  $g = [Drawing.Graphics]::FromImage($b); $g.CopyFromScreen($x, $y, 0, 0, $b.Size); $g.Dispose()
  $b.Save((Join-Path $outDir $name), [Drawing.Imaging.ImageFormat]::Png); $b.Dispose()
  "shot $name ${w}x$h"
}
try {
  $deadline = (Get-Date).AddSeconds(6)
  while ($p.MainWindowHandle -eq 0 -and -not $p.HasExited -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 100; $p.Refresh() }
  if (-not $p.HasExited) {
    [void][Win]::SetWindowPos($p.MainWindowHandle, [IntPtr](-1), 0, 0, 0, 0, 0x0003)
    [void][Win]::SetForegroundWindow($p.MainWindowHandle)
  }
  Start-Sleep -Seconds $Wait
  $p.Refresh()
  "exited=$($p.HasExited) title='$($p.MainWindowTitle)'"
  if ($Clip) { $ff = Start-Process ffmpeg -ArgumentList "-v error -y -f gdigrab -framerate 60 -draw_mouse 0 -t $ClipSec -i `"title=Storm of Gurba`" -c:v libx264 -preset ultrafast -crf 16 -pix_fmt yuv420p `"$outDir\$Clip`"" -PassThru -WindowStyle Hidden }
  $n = 0
  foreach ($k in ($Keys -split ',' | Where-Object { $_ })) {
    if ($p.HasExited) { break }
    $a = $k -split ':'
    if ($a[0] -notin 'SHOT','WAIT') {
      if (-not [Win]::Focus($p.MainWindowHandle)) { 'WARNING: the game is not in front, input not sent: ' + $k; continue }
      $rr = New-Object Win+R; [void][Win]::GetWindowRect($p.MainWindowHandle, [ref]$rr); [void][Win]::SetCursorPos(($rr.L + $rr.Rt) / 2, ($rr.T + $rr.B) / 2)
    }
    switch -Regex ($a[0]) {
      '^LMB$'   { [Win]::Click([int]($a[1] + '')) ; break }
      '^RMB$'   { [Win]::mouse_event(8, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds ([int]($a[1] + '')); [Win]::mouse_event(16, 0, 0, 0, [IntPtr]::Zero); break }
      '^CLICK$' { [void][Win]::SetCursorPos($rr.L + 8 + [int]$a[1], $rr.T + 31 + [int]$a[2]); Start-Sleep -Milliseconds 150; [Win]::Click(60); break }
      '^LDOWN$' { [Win]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); break }
      '^LUP$'   { [Win]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero); break }
      '^TURN$'  { [Win]::Turn([int]$a[1], [int]$a[2]); break }
      '^WAIT$'  { Start-Sleep -Milliseconds ([int]$a[1]); break }
      '^SHOT$'  { Shot(($Out -replace '\.png$', "_k$n.png")); $n++; break }
      default   { [Win]::Hold([byte][char]$a[0], [int]$a[1]) }
    }
  }
  for ($i = 0; $i -lt $Shots -and -not $p.HasExited; $i++) {
    $name = if ($Shots -gt 1) { $Out -replace '\.png$', "_$i.png" } else { $Out }
    Shot $name
    Start-Sleep -Milliseconds ([int]($Gap * 1000))
  }
} finally {
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force } else { "exit code: $($p.ExitCode)" }
}
$log = Join-Path $dir 'Startup.log'
if (Test-Path $log) { '--- end of log'; Get-Content $log -Tail 5 }

