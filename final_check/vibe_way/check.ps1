$d = $PSScriptRoot
$py = "python"
function Run($a) {
  $o = [IO.Path]::GetTempFileName(); $e = [IO.Path]::GetTempFileName()
  $p = Start-Process $py -ArgumentList (@("`"$d\main.py`"") + $a) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $o -RedirectStandardError $e
  [pscustomobject]@{code=$p.ExitCode; out=(Get-Content $o -Raw); err=(Get-Content $e -Raw)}
}
$sw = [Diagnostics.Stopwatch]::StartNew()
$r1 = Run @("--customer","`"  ada lovelace `"","--qty","3","--price","2.5")
$sw.Stop(); "local_run_ms=$($sw.ElapsedMilliseconds)"
"C1 code=$($r1.code) out=$($r1.out)"
$r1b = Run @("--customer","`"  ada lovelace `"","--qty","3","--price","2.5")
$r2 = Run @("--customer","`"   `"","--qty","1","--price","1")
"C2 code=$($r2.code) out=[$($r2.out)] err=$($r2.err)"
"C3 same=$($r1.out -eq $r1b.out)"
$r4 = Run @("--customer","bob","--qty","abc","--price","1")
"C4 code=$($r4.code) err=$($r4.err)"
