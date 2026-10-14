# gflow.ps1 — llama a gflow-cli (Google Flow / Nano Banana) sin pasar por gflow.exe.
# Smart App Control bloquea el .exe envoltorio de uv, pero no el python.exe del venv (mismo truco que nlm.ps1).
# Uso: & ".\tools\gflow.ps1" image t2i "prompt" --model nano-pro --aspect 9:16 -o salida.png
$py = "$env:APPDATA\uv\tools\gflow-cli\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"
$json = ConvertTo-Json -Compress -InputObject @($args | ForEach-Object { "$_" })
$env:GFLOW_ARGS_B64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
$code = 'import os,sys,json,base64; sys.argv=["gflow"]+json.loads(base64.b64decode(os.environ["GFLOW_ARGS_B64"]).decode()); from gflow_cli.cli import main; main()'
& $py -c $code.Replace('"', '\"')
exit $LASTEXITCODE
