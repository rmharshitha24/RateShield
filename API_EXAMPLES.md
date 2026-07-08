# RateShield API Examples

These examples use PowerShell. Keep the Flask server running in one terminal and run these commands in a second terminal.

## Health

```powershell
Invoke-RestMethod http://localhost:5000/health
```

## Create User

```powershell
$user = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5000/users" `
  -ContentType "application/json" `
  -Body '{"username":"alice","plan":"pro","rate_limit":{"algorithm":"token_bucket","max_requests":5,"time_window":60,"refill_rate":1,"bucket_capacity":5}}'

$apiKey = $user.data.api_key
$apiKey
```

## Call Protected Endpoint

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:5000/protected" `
  -Headers @{"X-API-Key"=$apiKey}
```

## Force Rate Limit

```powershell
1..10 | ForEach-Object {
  Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "http://localhost:5000/protected" `
    -Headers @{"X-API-Key"=$apiKey} `
    -ErrorAction SilentlyContinue
}
```

## Logs And Stats

```powershell
Invoke-RestMethod http://localhost:5000/logs
Invoke-RestMethod http://localhost:5000/stats
```
