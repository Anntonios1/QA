$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:5000/api'
$results = [System.Collections.Generic.List[object]]::new()

function Add-Result($name, $ok, $detail) {
    $results.Add([pscustomobject]@{
        Paso = $name
        Estado = if ($ok) { 'OK' } else { 'FAIL' }
        Detalle = $detail
    }) | Out-Null
}

function Invoke-Api {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [hashtable]$Headers = $null,
        [int[]]$Expect = @(200),
        [int]$TimeoutSec = 45,
        [int]$RetryOn429Count = 0,
        [int]$RetryDelaySec = 10
    )

    $uri = "$base$Path"
    $jsonBody = $null
    if ($null -ne $Body) {
        $jsonBody = ($Body | ConvertTo-Json -Depth 15)
    }

    $supportsSkipHttp = (Get-Command Invoke-WebRequest).Parameters.ContainsKey('SkipHttpErrorCheck')

    $attempt = 0
    $resp = $null
    $status = 0
    while ($true) {
        $attempt++

        $invokeParams = @{
            Uri = $uri
            Method = $Method
            Headers = $Headers
            ContentType = 'application/json'
            Body = $jsonBody
            TimeoutSec = $TimeoutSec
        }
        if ($supportsSkipHttp) {
            $invokeParams['SkipHttpErrorCheck'] = $true
        }

        try {
            $resp = Invoke-WebRequest @invokeParams
            $status = [int]$resp.StatusCode
        }
        catch {
            # En Windows PowerShell, los 4xx/5xx suelen lanzar excepcion.
            # Intentamos recuperar el status code y contenido de respuesta.
            $webResp = $_.Exception.Response
            if ($webResp -and $webResp.StatusCode) {
                $status = [int]$webResp.StatusCode
                $resp = [pscustomobject]@{
                    StatusCode = $status
                    Content = $null
                }
            }
            else {
                throw
            }
        }

        if ($status -eq 429 -and $attempt -le ($RetryOn429Count + 1)) {
            if ($attempt -le $RetryOn429Count) {
                Start-Sleep -Seconds $RetryDelaySec
                continue
            }
        }

        break
    }

    $parsed = $null
    if ($resp.Content) {
        try { $parsed = $resp.Content | ConvertFrom-Json -Depth 15 } catch { $parsed = $resp.Content }
    }

    $ok = $Expect -contains $status
    Add-Result $Name $ok "HTTP $status (intento $attempt)"

    return [pscustomobject]@{ Status = $status; Json = $parsed }
}

$ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$email = "audit.$ts@example.com"
$pass = 'Audit123!'
$nombre = 'QA Auditor'

$null = Invoke-Api -Name 'Registro usuario' -Method 'POST' -Path '/auth/registro' -Body @{ nombre = $nombre; email = $email; password = $pass } -Expect @(201) -RetryOn429Count 4 -RetryDelaySec 15
$login = Invoke-Api -Name 'Login usuario' -Method 'POST' -Path '/auth/login' -Body @{ email = $email; password = $pass } -Expect @(200) -RetryOn429Count 4 -RetryDelaySec 15

$access = $login.Json.data.tokens.access_token
$refresh = $login.Json.data.tokens.refresh_token
if (-not $access) { throw 'No se recibio access_token' }
if (-not $refresh) { throw 'No se recibio refresh_token' }

$auth = @{ Authorization = "Bearer $access" }

$catsResp = Invoke-Api -Name 'Listar categorias' -Method 'GET' -Path '/categorias' -Headers $auth -Expect @(200)
$catIng = ($catsResp.Json.data | Where-Object { $_.tipo -eq 'ingreso' } | Select-Object -First 1).id
$catGas = ($catsResp.Json.data | Where-Object { $_.tipo -eq 'gasto' } | Select-Object -First 1).id
if (-not $catIng -or -not $catGas) { throw 'No se encontraron categorias de ingreso/gasto' }

Invoke-Api -Name 'Balance inicial' -Method 'GET' -Path '/balance' -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Resumen 30 dias' -Method 'GET' -Path '/resumen?dias=30' -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Notificaciones no leidas' -Method 'GET' -Path '/notificaciones?no_leidas=true' -Headers $auth -Expect @(200) | Out-Null

$movIn = Invoke-Api -Name 'Crear movimiento ingreso' -Method 'POST' -Path '/movimientos' -Headers $auth -Body @{ categoria_id = $catIng; tipo = 'ingreso'; monto = 1500.75; descripcion = 'Ingreso auditoria' } -Expect @(201)
$movGa = Invoke-Api -Name 'Crear movimiento gasto' -Method 'POST' -Path '/movimientos' -Headers $auth -Body @{ categoria_id = $catGas; tipo = 'gasto'; monto = 250.10; descripcion = 'Gasto auditoria' } -Expect @(201)
$movId = $movGa.Json.data.id

# Pruebas de inyeccion de dinero/manipulacion de monto
Invoke-Api -Name 'Inyeccion dinero monto NaN' -Method 'POST' -Path '/movimientos' -Headers $auth -Body @{ categoria_id = $catIng; tipo = 'ingreso'; monto = 'NaN'; descripcion = 'Intento inyeccion NaN' } -Expect @(422) | Out-Null
Invoke-Api -Name 'Inyeccion dinero monto Infinity' -Method 'POST' -Path '/movimientos' -Headers $auth -Body @{ categoria_id = $catIng; tipo = 'ingreso'; monto = 'Infinity'; descripcion = 'Intento inyeccion Infinity' } -Expect @(422) | Out-Null
Invoke-Api -Name 'Inyeccion dinero sobre limite' -Method 'POST' -Path '/movimientos' -Headers $auth -Body @{ categoria_id = $catIng; tipo = 'ingreso'; monto = 1000000000; descripcion = 'Intento inyeccion sobre limite' } -Expect @(422) | Out-Null
Invoke-Api -Name 'Inyeccion dinero SQL-like' -Method 'POST' -Path '/movimientos' -Headers $auth -Body @{ categoria_id = $catIng; tipo = 'ingreso'; monto = '1;DROP TABLE movimientos'; descripcion = 'Intento SQL-like' } -Expect @(422) | Out-Null

Invoke-Api -Name 'Listar movimientos' -Method 'GET' -Path '/movimientos?limite=100' -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Filtro invalido monto_min>monto_max' -Method 'GET' -Path '/movimientos?monto_min=100&monto_max=10' -Headers $auth -Expect @(400) | Out-Null
Invoke-Api -Name 'Editar movimiento gasto' -Method 'PUT' -Path "/movimientos/$movId" -Headers $auth -Body @{ descripcion = 'Gasto auditoria editado'; monto = 275.55 } -Expect @(200) | Out-Null
Invoke-Api -Name 'Exportar movimientos CSV' -Method 'GET' -Path '/movimientos/export/csv' -Headers $auth -Expect @(200) | Out-Null

$mes = Get-Date -Format 'yyyy-MM-01'
$pres = Invoke-Api -Name 'Crear presupuesto' -Method 'POST' -Path '/presupuestos' -Headers $auth -Body @{ categoria_id = $catGas; monto_limite = 1000; mes = $mes } -Expect @(201)
$presId = $pres.Json.data.id
Invoke-Api -Name 'Listar presupuestos' -Method 'GET' -Path "/presupuestos?mes=$mes" -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Verificar presupuesto' -Method 'GET' -Path "/presupuestos/verificar?categoria_id=$catGas&mes=$mes" -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Eliminar presupuesto' -Method 'DELETE' -Path "/presupuestos/$presId" -Headers $auth -Expect @(200) | Out-Null

$hoy = Get-Date -Format 'yyyy-MM-dd'
$rec = Invoke-Api -Name 'Crear recurrencia' -Method 'POST' -Path '/recurrencias' -Headers $auth -Body @{ categoria_id = $catGas; tipo = 'gasto'; monto = 99.99; descripcion = 'Subscripcion QA'; frecuencia = 'mensual'; dia_ejecucion = 15; proxima_fecha = $hoy } -Expect @(201)
$recId = $rec.Json.data.id
Invoke-Api -Name 'Listar recurrencias' -Method 'GET' -Path '/recurrencias' -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Ejecutar recurrencias pendientes' -Method 'POST' -Path '/recurrencias/ejecutar' -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Desactivar recurrencia' -Method 'DELETE' -Path "/recurrencias/$recId" -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Reactivar recurrencia' -Method 'POST' -Path "/recurrencias/$recId/reactivar" -Headers $auth -Body @{ proxima_fecha = $hoy } -Expect @(200) | Out-Null

Invoke-Api -Name 'Security status' -Method 'GET' -Path '/security/status' -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Security encrypt test' -Method 'POST' -Path '/security/encrypt-test' -Headers $auth -Body @{ texto = 'Prueba de cifrado auditoria' } -Expect @(200) | Out-Null

Invoke-Api -Name 'IA perfil' -Method 'GET' -Path '/ai/perfil' -Headers $auth -Expect @(200, 503) -TimeoutSec 90 | Out-Null
Invoke-Api -Name 'IA daily insight' -Method 'POST' -Path '/ai/daily-insight' -Headers $auth -Expect @(200, 503) -TimeoutSec 90 | Out-Null
Invoke-Api -Name 'Chat IA' -Method 'POST' -Path '/chat' -Headers $auth -Body @{ mensaje = 'Dame un consejo financiero breve' } -Expect @(200, 503) -TimeoutSec 90 | Out-Null

Invoke-Api -Name 'OCR base64 invalida' -Method 'POST' -Path '/ocr/recibo' -Headers $auth -Body @{ imagen = 'not-base64' } -Expect @(400) | Out-Null

$tinyPngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5nQAAAAASUVORK5CYII='
$ocrHybrid = Invoke-Api -Name 'OCR hibrido texto_prueba' -Method 'POST' -Path '/ocr/recibo' -Headers $auth -Body @{
    imagen = $tinyPngBase64
    texto_prueba = 'TIENDA QA\nFecha: 2026-04-15\nTotal: 123.45\nGracias'
} -Expect @(200)

$ocrHybridOk = $false
try {
    $ocrHybridOk = (
        $ocrHybrid.Status -eq 200 -and
        [decimal]$ocrHybrid.Json.data.total -eq [decimal]123.45 -and
        $ocrHybrid.Json.data.modo_prueba -eq $true
    )
} catch {
    $ocrHybridOk = $false
}
Add-Result 'OCR hibrido parse total en testing' $ocrHybridOk "total=$($ocrHybrid.Json.data.total) modo_prueba=$($ocrHybrid.Json.data.modo_prueba)"

$ocrNequi = Invoke-Api -Name 'OCR hibrido texto_prueba Nequi' -Method 'POST' -Path '/ocr/recibo' -Headers $auth -Body @{
    imagen = $tinyPngBase64
    texto_prueba = 'Comprobante de pago Envio Realizado Para Nataly Grueso Cuanto 7000,00 Numero Nequi 324 497 8875 Fecha 06 de abril de 2026 a las 06:27 p m Referencia M19781481'
} -Expect @(200)

$ocrNequiOk = $false
try {
    $ocrNequiOk = (
        $ocrNequi.Status -eq 200 -and
        [decimal]$ocrNequi.Json.data.total -eq [decimal]7000.00 -and
        $ocrNequi.Json.data.fecha -eq '2026-04-06' -and
        $ocrNequi.Json.data.tipo_sugerido -eq 'gasto'
    )
} catch {
    $ocrNequiOk = $false
}
Add-Result 'OCR Nequi parse total/fecha/tipo en testing' $ocrNequiOk "total=$($ocrNequi.Json.data.total) fecha=$($ocrNequi.Json.data.fecha) tipo=$($ocrNequi.Json.data.tipo_sugerido) descripcion=$($ocrNequi.Json.data.descripcion)"

$refresh1 = Invoke-Api -Name 'Refresh token primer uso' -Method 'POST' -Path '/auth/refresh' -Body @{ refresh_token = $refresh } -Expect @(200)
$newRefresh = $refresh1.Json.data.refresh_token
Invoke-Api -Name 'Refresh token reutilizado' -Method 'POST' -Path '/auth/refresh' -Body @{ refresh_token = $refresh } -Expect @(401) | Out-Null
Invoke-Api -Name 'Revoke refresh token nuevo' -Method 'POST' -Path '/auth/revoke' -Headers $auth -Body @{ refresh_token = $newRefresh } -Expect @(200) | Out-Null
Invoke-Api -Name 'Refresh token revocado' -Method 'POST' -Path '/auth/refresh' -Body @{ refresh_token = $newRefresh } -Expect @(401) | Out-Null

Invoke-Api -Name 'Logout' -Method 'POST' -Path '/auth/logout' -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Eliminar movimiento ingreso' -Method 'DELETE' -Path "/movimientos/$($movIn.Json.data.id)" -Headers $auth -Expect @(200) | Out-Null
Invoke-Api -Name 'Eliminar movimiento gasto' -Method 'DELETE' -Path "/movimientos/$movId" -Headers $auth -Expect @(200) | Out-Null

$okCount = ($results | Where-Object { $_.Estado -eq 'OK' }).Count
$failCount = ($results | Where-Object { $_.Estado -eq 'FAIL' }).Count

Write-Output '=== RESUMEN AUDITORIA API ==='
[pscustomobject]@{
    Total = $results.Count
    OK = $okCount
    FAIL = $failCount
    UsuarioAudit = $email
} | Format-List | Out-String | Write-Output

Write-Output '=== DETALLE ==='
$results | Format-Table -AutoSize | Out-String | Write-Output

if ($failCount -gt 0) {
    exit 2
}
