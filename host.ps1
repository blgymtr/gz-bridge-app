# Easy FPS Editor'ün kendi sınıflarını çalıştırır. 32 bit PowerShell ister. Editör penceresi açmaz.
# Kullanım: host.ps1 -Exe <EasyFPSEditor_CE.exe> -Proje <klasör\> -Is dump
#           host.ps1 ... -Is apply -Ops <işlem.json>      (kopru.py üretir)
param([string]$Exe, [string]$Proje, [string]$Is, [string]$Ops = '', [string]$SaveTo = '')
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding $false
$engine = Split-Path $Exe
[Environment]::CurrentDirectory = $engine
Set-Location -LiteralPath $engine
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[void][Reflection.Assembly]::LoadFrom($Exe)
if (-not $Proje.EndsWith('\')) { $Proje += '\' }
$res = New-Object EasyFPSEditor15.Resources
if (-not $res.LoadAllResources($Proje)) { throw 'Editor projeyi yukleyemedi' }

$LISTS = @{ enemies = 'ResourceEnemy'; decorations = 'ResourceDecoration'; weapons = 'ResourceWeapon'; maps = 'ResourceMap'; hps = 'ResourceHp'; armours = 'ResourceArmour'; animations = 'ResourceAnimation'; models = 'ResourceModel'; textures = 'ResourceTexture'; tiles = 'ResourceTile' }
$SINGLES = 'game', 'player', 'hud'

function ToPlain($o) {
  $h = [ordered]@{}
  foreach ($f in $o.GetType().GetFields([Reflection.BindingFlags]'Public,Instance')) {
    $v = $f.GetValue($o)
    if ($null -eq $v) { continue }
    $t = $f.FieldType
    if ($t.IsPrimitive -or $t -eq [string]) { $h[$f.Name] = $v }
    elseif ($t.IsEnum) { $h[$f.Name] = [int]$v }
    elseif ($t.IsArray -and ($t.GetElementType().IsPrimitive -or $t.GetElementType() -eq [string])) { $h[$f.Name] = @($v) }
    elseif ($t -eq [Drawing.Color]) { $h[$f.Name] = @($v.R, $v.G, $v.B, $v.A) }
  }
  return $h
}

function SetField($o, $name, $val) {
  $arrIdx = -1
  if ($name -match '^(\w+)\[(\d+)\]$') { $name = $Matches[1]; $arrIdx = [int]$Matches[2] }
  $f = $o.GetType().GetField($name)
  if (-not $f) { throw "alan yok: $name" }
  $t = $f.FieldType
  if ($arrIdx -ge 0) { $a = $f.GetValue($o); $a[$arrIdx] = [Convert]::ChangeType($val, $t.GetElementType(), [Globalization.CultureInfo]::InvariantCulture); return }
  if ($t.IsArray) { $e = $t.GetElementType(); $arr = [Array]::CreateInstance($e, $val.Count); for ($i = 0; $i -lt $val.Count; $i++) { $arr[$i] = [Convert]::ChangeType($val[$i], $e, [Globalization.CultureInfo]::InvariantCulture) }; $f.SetValue($o, $arr); return }
  if ($t -eq [bool]) { $f.SetValue($o, ($val -eq $true -or "$val" -in '1', 'true', 'True')); return }
  if ($t.IsEnum) { $f.SetValue($o, [Enum]::ToObject($t, [int]$val)); return }
  $f.SetValue($o, [Convert]::ChangeType($val, $t, [Globalization.CultureInfo]::InvariantCulture))
}

function Target($coll, $key) {
  if ($coll -in $SINGLES) { return $res.$coll }
  $list = $res.$coll
  if ("$key" -match '^\d+$') { return $list[[int]$key] }
  foreach ($x in $list) { $n = if ($x.GetType().GetField('entityName')) { $x.entityName } else { $x.name }; if ($n -eq $key) { return $x } }
  throw "$coll icinde bulunamadi: $key"
}

if ($Is -eq 'apply') {
  $list = Get-Content -LiteralPath $Ops -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($op in @($list)) {
    switch ($op.op) {
      'set' { $o = Target $op.coll $op.key; foreach ($p in $op.fields.PSObject.Properties) { SetField $o $p.Name $p.Value } }
      'add' {
        $o = New-Object ('EasyFPSEditor15.' + $LISTS[$op.coll])
        if ($op.coll -in 'enemies', 'decorations') { $o.id = $o.GetType()::freeId; $o.GetType()::freeId = $o.id + 1 }
        foreach ($p in $op.fields.PSObject.Properties) { SetField $o $p.Name $p.Value }
        if ($op.coll -eq 'weapons') {
          $i = 0; while ($i -lt $res.weapons.Count -and $res.weapons[$i].name -ne 'None') { $i++ }
          if ($i -ge 8) { throw '8 silah dolu' }
          $res.weapons[$i] = $o
        } else { [void]$res.$($op.coll).Add($o) }
      }
      'del' {
        $o = Target $op.coll $op.key
        if ($op.coll -eq 'weapons') { [void]$res.weapons.Remove($o); [void]$res.weapons.Add((New-Object EasyFPSEditor15.ResourceWeapon)) } else { [void]$res.$($op.coll).Remove($o) }
      }
      'order' {
        # verilen adlar listenin başına, verildiği sırayla
        $names = @($op.names); [array]::Reverse($names)
        foreach ($nm in $names) { $o = Target $op.coll $nm; [void]$res.$($op.coll).Remove($o); $res.$($op.coll).Insert(0, $o) }
      }
      default { throw "bilinmeyen islem $($op.op)" }
    }
  }
  $out = if ($SaveTo) { if ($SaveTo.EndsWith('\')) { $SaveTo } else { $SaveTo + '\' } } else { $Proje }
  [void]$res.SaveAllResources($out)
  'KAYDEDILDI'
  return
}

$d = [ordered]@{}
foreach ($c in $LISTS.Keys) { $d[$c] = @($res.$c | ForEach-Object { ToPlain $_ }) }
foreach ($c in $SINGLES) { $d[$c] = ToPlain $res.$c }
$d | ConvertTo-Json -Depth 5 -Compress
