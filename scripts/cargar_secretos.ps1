# Sube a GitHub, como secretos cifrados del repo, las claves de .env y el perfil de profile.md.
# Uso (desde la carpeta del proyecto):  powershell -ExecutionPolicy Bypass -File scripts\cargar_secretos.ps1
# Requiere GitHub CLI (gh) con sesión iniciada. Los valores se pasan por la entrada estándar, no por la línea de comandos.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) { throw "No encuentro .env en $root" }

$values = @{}
foreach ($line in Get-Content $envFile -Encoding UTF8) {
    $t = $line.Trim()
    if ($t -eq "" -or $t.StartsWith("#") -or -not $t.Contains("=")) { continue }
    $k, $v = $t.Split("=", 2)
    $values[$k.Trim()] = $v.Trim().Trim('"').Trim("'")
}

foreach ($name in "GEMINI_API_KEY", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO") {
    if (-not $values[$name]) { throw "Falta $name en .env" }
    $values[$name] | gh secret set $name
    Write-Host "Secreto $name guardado"
}

$profile = Join-Path $root "profile.md"
if (Test-Path $profile) {
    Get-Content $profile -Raw -Encoding UTF8 | gh secret set PROFILE_TEXT
    Write-Host "Secreto PROFILE_TEXT guardado"
}

if ($values["MIN_SALARY_CLP"]) {
    gh variable set MIN_SALARY_CLP --body $values["MIN_SALARY_CLP"]
    Write-Host "Variable MIN_SALARY_CLP = $($values['MIN_SALARY_CLP'])"
}

Write-Host "`nListo. Lanza una prueba con:  gh workflow run daily.yml -f dry_run=true"
