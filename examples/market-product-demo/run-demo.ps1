param(
    [int]$Duration = 10,
    [int]$Workers = 4,
    [string]$OutputDir = "reports\market-demo"
)

$ErrorActionPreference = "Stop"
$DemoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $DemoRoot "..\..")
$SchemaPath = Join-Path $DemoRoot "schema.sql"
$SeedPath = Join-Path $DemoRoot "sample_data.sql"
$ReportDir = Join-Path $RepoRoot $OutputDir

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

Write-Host "== DataWraith Market Product Demo =="
Write-Host "Repo: $RepoRoot"
Write-Host "Reports: $ReportDir"
Write-Host ""

Write-Host "== Runtime doctor =="
sdb doctor

Write-Host ""
Write-Host "== Load demo schema =="
sdb init $SchemaPath --execute

Write-Host ""
Write-Host "== Load demo sample data =="
sdb init $SeedPath --execute

Write-Host ""
Write-Host "== Concurrency: products.stock =="
sdb attack concurrency --execute --table products --column stock --duration $Duration --workers $Workers --updates 80 --output (Join-Path $ReportDir "concurrency.json")

Write-Host ""
Write-Host "== R/W-heavy workload =="
sdb attack rw-heavy --execute --duration $Duration --workers $Workers --row-count 100 --operations 300 --output (Join-Path $ReportDir "rw-heavy.json")

Write-Host ""
Write-Host "== Migration-lock workload =="
sdb attack migration --execute --table products --column market_demo_flag --duration $Duration --workers 2 --row-count 100 --operations 200 --output (Join-Path $ReportDir "migration.json")

Write-Host ""
Write-Host "== Security/isolation workload =="
sdb attack security --execute --duration $Duration --tenants 3 --rows-per-tenant 5 --fuzz-payloads 8 --output (Join-Path $ReportDir "security.json")

Write-Host ""
Write-Host "== Export security reports =="
sdb report (Join-Path $ReportDir "security.json") --format sarif --output (Join-Path $ReportDir "security.sarif")
sdb report (Join-Path $ReportDir "security.json") --format junit --output (Join-Path $ReportDir "security.xml")
sdb report (Join-Path $ReportDir "security.json") --format pdf --output (Join-Path $ReportDir "security.pdf")

Write-Host ""
Write-Host "== Compare concurrency vs rw-heavy =="
sdb compare (Join-Path $ReportDir "concurrency.json") (Join-Path $ReportDir "rw-heavy.json")

Write-Host ""
Write-Host "Demo complete. Open reports in: $ReportDir"
