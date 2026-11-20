param($dir)
$py="python"
$ErrorActionPreference="Continue"
function Run($a){ $sw=[Diagnostics.Stopwatch]::StartNew(); $o=& $py "$dir\main.py" @a 2>"$dir\err.tmp"; $c=$LASTEXITCODE; $sw.Stop(); [pscustomobject]@{out=($o -join "`n");err=([string](Get-Content "$dir\err.tmp" -Raw -ErrorAction SilentlyContinue)).Trim();code=$c;ms=$sw.Elapsed.TotalMilliseconds} }
$r1=Run @('--customer','  ada lovelace ','--qty','3','--price','2.5')
$r1b=Run @('--customer','  ada lovelace ','--qty','3','--price','2.5')
$r2=Run @('--customer','   ','--qty','1','--price','1')
$r4=Run @('--customer','x','--qty','abc','--price','1')
$c1 = ($r1.code -eq 0 -and $r1.out -eq '{"customer": "Ada Lovelace", "total": "$7.50"}')
$c2 = ($r2.code -eq 1 -and -not $r2.out -and $r2.err.Trim().Length -gt 0)
$c3 = ($r1.out -eq $r1b.out -and $r1.code -eq $r1b.code -and $r1.code -eq 0)
$c4 = ($r4.code -eq 1 -and $r4.err.Trim().Length -gt 0)
[pscustomobject]@{C1=$c1;C2=$c2;C3=$c3;C4=$c4;runMs=$r1.ms;r1o=$r1.out;r1e=$r1.err;r1c=$r1.code;r2c=$r2.code;r2o=$r2.out;r2e=$r2.err;r4c=$r4.code;r4o=$r4.out;r4e=$r4.err} | ConvertTo-Json

