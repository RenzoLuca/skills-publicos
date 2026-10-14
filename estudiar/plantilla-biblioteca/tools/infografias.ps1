# Genera la infografía (Nano Banana Pro vía Google Flow) de cada ficha de una carpeta de la biblioteca.
#
#   .\infografias.ps1 -Carpeta "..\biblioteca\videos\canal-titulo"              # las que falten
#   .\infografias.ps1 -Carpeta "..." -Archivos 02-habitos,03-identidad           # rehacer esas
#
# Cada ficha NN-titulo.md lleva un bloque ```infografia (formato en el skill /estudiar): titulo, ancla, motor,
# puntos "- etiqueta | apoyo", accion, preguntas "? ...", visual. Diseño: metodo.md -> Infografía.
# El texto va dictado palabra por palabra: Nano Banana no redacta nada.
# Abre Chrome visible ~1-2 min por pedido. Pausa de 2-4 min entre pedidos (seguridad de la cuenta).
# Se detiene al primer fallo para no insistir. Guarda NN-titulo.jpg (~0,7 MB, 768x1376).
param(
  [Parameter(Mandatory)][string]$Carpeta,
  [string[]]$Archivos = @(),
  [switch]$SoloPrompt,  # muestra el prompt sin generar (no abre Chrome)
  [ValidateSet('9:16', '16:9')][string]$Aspecto = '9:16'   # 16:9 = diapositiva de Google Slides / PowerPoint
)
$forma = if ($Aspecto -eq '16:9') { 'horizontal 16:9 (diapositiva)' } else { 'vertical 9:16' }
$ErrorActionPreference = 'Stop'
$gflow = Join-Path $PSScriptRoot 'gflow.ps1'

# Estilo fijo de toda la biblioteca (cámbialo solo aquí).
$estilo = 'infografía editorial moderna, ilustraciones vectoriales limpias con algo de profundidad, fondo blanco hueso, texto azul marino, un solo color de acento ámbar, títulos en sans-serif geométrica gruesa, ilustraciones con función explicativa, mucho espacio en blanco, look de revista premium'

$fichas = Get-ChildItem $Carpeta -Filter '*.md' | Where-Object { $_.BaseName -match '^\d\d-' } | Sort-Object Name
if ($Archivos) { $fichas = $fichas | Where-Object { $Archivos -contains $_.BaseName } }
else { $fichas = $fichas | Where-Object { -not (Test-Path (Join-Path $Carpeta "$($_.BaseName).jpg")) } }
$fichas = @($fichas)
if (-not $fichas) { Write-Host 'Nada que generar.'; exit 0 }

$n = 0
foreach ($f in $fichas) {
  $md = Get-Content $f.FullName -Raw -Encoding UTF8
  if ($md -notmatch '(?s)```infografia\s*(.+?)```') { Write-Host "Sin bloque infografia: $($f.Name) (salto)"; continue }
  $bloque = $Matches[1]
  function Campo($k) { if ($bloque -match "(?m)^${k}:\s*(.+)$") { $Matches[1].Trim() } }
  $titulo = Campo 'titulo'; if (-not $titulo) { throw "Falta titulo: en $($f.Name)" }
  $ancla = Campo 'ancla'; $motor = Campo 'motor'; $accion = Campo 'accion'
  $visual = Campo 'visual'; if (-not $visual) { $visual = 'una ilustración que explique cada punto' }
  $puntos = @([regex]::Matches($bloque, '(?m)^-\s*(.+)$') | ForEach-Object { $_.Groups[1].Value.Trim() })
  $preguntas = @([regex]::Matches($bloque, '(?m)^\?\s*(.+)$') | ForEach-Object { $_.Groups[1].Value.Trim() })
  # "- etiqueta | apoyo": si no le dictamos el apoyo, Nano Banana inventa un párrafo (prueba 2026-10-10).
  $lista = ($puntos | ForEach-Object -Begin { $i = 0 } -Process {
    $i++; $par = $_ -split '\s*\|\s*', 2
    if ($par.Count -eq 2) { "$i) etiqueta en negrita `"$($par[0])`" y pegada a ella, más chica, `"$($par[1])`"" } else { "$i) etiqueta en negrita `"$_`"" }
  }) -join '; '

  # Diseño según metodo.md (Mayer: sin párrafos, contigüidad, coherencia, señalización; grilla de 1 página).
  # Prompt en español: con el prompt en inglés, Nano Banana TRADUJO el texto (prueba del 2026-10-10).
  $prompt = "Póster infográfico $forma en ESPAÑOL para recordar lo aprendido. Estilo: $estilo. " +
    "Escribe EXACTAMENTE este texto, en español, letra por letra y con tildes. NO lo traduzcas. " +
    "NO agregues ninguna otra palabra, rótulo, párrafo ni explicación propia: este es TODO el texto. " +
    "ARRIBA: el título `"$titulo`"" + $(if ($ancla) { " junto a una ilustración principal grande que resume la idea central (sin texto; NO dibujes un ancla de barco): $ancla" }) + ". " +
    "AL CENTRO: un diagrama que conecte las ideas con flechas" + $(if ($motor) { " ($motor)" }) + "; EXACTAMENTE $($puntos.Count) nodos, ni uno más ni uno menos (no repitas ni inventes nodos); cada nodo tiene su ilustración y su texto pegado a ella: $lista. " +
    "Cada ilustración debe explicar su idea (nada decorativo). Color de acento para resaltar las conexiones. " +
    $(if ($accion) { "Un recuadro destacado con el texto `"$accion`". " }) +
    $(if ($preguntas) { "ABAJO: una franja titulada `"Repasa sin mirar`" con estas preguntas: " + (($preguntas | ForEach-Object { "`"$_`"" }) -join ' y ') + ". " }) +
    "Ilustraciones (sin texto): $visual. Texto grande y legible, márgenes amplios, nada cortado en los bordes."
  if ($SoloPrompt) { Write-Host "--- $($f.BaseName)`n$prompt"; continue }
  if ($n -gt 0) { Start-Sleep -Seconds (Get-Random -Minimum 120 -Maximum 240) }
  $n++
  # gflow guarda <media>_1.jpg dentro de --out (con -o no escribe nada): carpeta temporal y se renombra.
  $tmp = Join-Path $env:TEMP "infografia-$($f.BaseName)"
  New-Item -ItemType Directory -Force $tmp | Out-Null
  Write-Host ("[{0}] {1}" -f (Get-Date -Format HH:mm), $f.BaseName)
  # gflow escribe su log por stderr: en PowerShell 5.1 con 'Stop' eso aborta el script
  $ErrorActionPreference = 'Continue'
  & $gflow image t2i $prompt --model nano-pro --aspect $Aspecto --out $tmp 2>$null | Out-Null
  $code = $LASTEXITCODE
  $ErrorActionPreference = 'Stop'
  $img = Get-ChildItem $tmp -Include *.jpg, *.png -Recurse | Select-Object -First 1
  if ($code -ne 0 -or -not $img) { [IO.Directory]::Delete($tmp, $true); Write-Host "gflow falló (exit $code) - paro para no insistir."; exit 1 }

  # (borrar con [IO.Directory]::Delete: Remove-Item falla con rutas cortas tipo USUARI~1)
  $jpg = Join-Path $Carpeta "$($f.BaseName).jpg"
  Move-Item $img.FullName $jpg -Force
  [IO.Directory]::Delete($tmp, $true)
  Write-Host "  -> $jpg"
}
Write-Host "Listo: $n infografías."
