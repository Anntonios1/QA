
$headers = @{
    "Authorization" = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcl9pZCI6MSwibm9tYnJlIjoidGVzdCIsImVtYWlsIjoidGVzdEBtYWlsLmNvbSIsInRpcG8iOiJhY2Nlc3MiLCJpYXQiOjE3Nzg3MDI4MTUsImV4cCI6MTc3ODcwMzcxNSwianRpIjoiMzIwMTZjOWFmZTYxMWUxZjdmMmYxY2U1ZWM3OWQ3ZGYifQ.xuMrPLYo41Jd0Xtkzvjbfk3FAWaGwve-SXMenaGh1ng"
    "Content-Type"  = "application/json"
}

function Test-Endpoint {
    param($Name, $Method, $Path, $Body = $null)
    Write-Host "`n--- Testing: $Name ($Method $Path) ---" -ForegroundColor Cyan
    try {
        $params = @{
            Uri     = "http://localhost:5000/api$Path"
            Method  = $Method
            Headers = $headers
        }
        if ($Body) { $params.Body = ($Body | ConvertTo-Json) }
        
        $resp = Invoke-RestMethod @params
        Write-Host "SUCCESS: $($resp.mensaje)" -ForegroundColor Green
        return $resp
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
             $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
             $errorBody = $reader.ReadToEnd()
             Write-Host "Error Body: $errorBody" -ForegroundColor Yellow
        }
        return $null
    }
}

# 1. Categorías
$cat = Test-Endpoint "Crear Categoría" "POST" "/categorias" @{ nombre="Transporte"; tipo="gasto"; icono="car" }
$catId = $cat.data.id

# 2. Movimientos
$mov = Test-Endpoint "Crear Movimiento" "POST" "/movimientos" @{ monto=2500; tipo="gasto"; categoria_id=$catId; descripcion="Gasolina Smoke Test"; fecha="2026-05-13" }
$movId = $mov.data.id

# 3. Listar Movimientos
$list = Test-Endpoint "Listar Movimientos" "GET" "/movimientos"

# 4. Balance
$balance = Test-Endpoint "Obtener Balance" "GET" "/balance"

# 5. Resumen
$resumen = Test-Endpoint "Obtener Resumen" "GET" "/resumen"

# 6. Presupuestos
Test-Endpoint "Crear Presupuesto" "POST" "/presupuestos" @{ categoria_id=$catId; monto_limite=5000; mes="2026-05-01" }

# 7. IA Chat
Test-Endpoint "Chat IA" "POST" "/chat" @{ mensaje="¿Cuánto gasté en gasolina?" }

# 8. IA Perfil
Test-Endpoint "Perfil IA" "GET" "/ai/perfil"

# 9. Notificaciones
Test-Endpoint "Notificaciones" "GET" "/notificaciones"

# 10. Limpieza (Opcional - Eliminar movimiento)
if ($movId) {
    Test-Endpoint "Eliminar Movimiento" "DELETE" "/movimientos/$movId"
}
