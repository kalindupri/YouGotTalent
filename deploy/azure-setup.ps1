#Requires -Version 5.1
<#
.SYNOPSIS
    One-time Azure infrastructure provisioning + initial deployment for YouGotTalent.
.DESCRIPTION
    Creates: resource group, budget alert, blob storage, PostgreSQL Flexible Server,
    Container Apps environment, then builds and deploys the backend and frontend.

    Prerequisites
    -------------
    - Azure CLI  : https://learn.microsoft.com/cli/azure/install-azure-cli-windows
    - Docker Desktop (running)
    - GitHub PAT  with scopes: read:packages, write:packages, delete:packages

    Run once from a PowerShell 5.1+ terminal:
        cd <repo-root>
        .\deploy\azure-setup.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================
# 1. Variables — EDIT THESE before running anything else
# ============================================================
$ResourceGroup      = "rg-ygt-dev"
$Location           = "australiaeast"        # change if region is restricted on your account
$DbServerName       = "ygt-pg-dev"           # must be globally unique across Azure
$DbAdminUser        = "ygtadmin"
$DbAdminPassword    = "ChangeMe123!ReplaceMe" # use a strong password — don't commit this
$DbName             = "ygt"
$StorageAccountName = "ygtdevstorage001"     # globally unique, lowercase, 3-24 chars, no dashes
$ContainerAppsEnv   = "ygt-env"
$BackendAppName     = "ygt-backend"
$FrontendAppName    = "ygt-frontend"
$AlertEmail         = "kalindu.pri@gmail.com"
$GithubUsername     = "<github-username>"    # EDIT: your GitHub username (lowercase)

# ============================================================
# Prompt for secrets up-front so the rest of the script runs unattended
# ============================================================
$GhcrPat = Read-Host "GitHub PAT (read:packages + write:packages scope)"

# Cryptographically-random SECRET_KEY — save this value for redeployments
$SecretKeyBytes = [System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
$SecretKey      = [System.Convert]::ToBase64String($SecretKeyBytes)

Write-Host ""
Write-Host "Generated SECRET_KEY (save this securely — e.g. GitHub Actions secret):" -ForegroundColor Yellow
Write-Host "  $SecretKey" -ForegroundColor Yellow
Write-Host ""

# Derive repo root from the script's own location (script lives in deploy/)
$RepoRoot = Split-Path $PSScriptRoot -Parent

# ============================================================
# 2. Resource group
# ============================================================
Write-Host "[2/12] Creating resource group '$ResourceGroup'..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location

# ============================================================
# 3. Budget alert  (set up BEFORE any billable resources)
# ============================================================
Write-Host "[3/12] Creating budget alert..." -ForegroundColor Cyan

# Add the consumption extension if it isn't already installed
az extension add --name consumption --only-show-errors 2>$null

$StartDate = (Get-Date -Day 1).ToString("yyyy-MM-dd")

# Write notifications JSON to a temp file to sidestep PowerShell ↔ az-CLI quoting issues
$NotifFile = New-TemporaryFile
@"
{
  "Actual_GreaterThan_50_Percent": {
    "enabled": true,
    "operator": "GreaterThan",
    "threshold": 50,
    "contactEmails": ["$AlertEmail"],
    "thresholdType": "Actual"
  },
  "Actual_GreaterThan_90_Percent": {
    "enabled": true,
    "operator": "GreaterThan",
    "threshold": 90,
    "contactEmails": ["$AlertEmail"],
    "thresholdType": "Actual"
  }
}
"@ | Set-Content -Path $NotifFile.FullName -Encoding UTF8

az consumption budget create `
    --budget-name    "ygt-dev-budget" `
    --resource-group $ResourceGroup `
    --amount         180 `
    --category       cost `
    --time-grain     Monthly `
    --start-date     $StartDate `
    --end-date       "2027-01-01" `
    --notifications  "@$($NotifFile.FullName)"

Remove-Item $NotifFile.FullName -ErrorAction SilentlyContinue

# ============================================================
# 4. Storage account + blob container for talent media
# ============================================================
Write-Host "[4/12] Creating storage account '$StorageAccountName'..." -ForegroundColor Cyan
az storage account create `
    --name         $StorageAccountName `
    --resource-group $ResourceGroup `
    --location     $Location `
    --sku          Standard_LRS `
    --kind         StorageV2 `
    --access-tier  Hot

# --public-access blob: individual blob URLs are publicly readable without SAS tokens,
# which matches how the app stores plain media URLs
az storage container create `
    --account-name $StorageAccountName `
    --name         "talent-media" `
    --auth-mode    login `
    --public-access blob

# ============================================================
# 5. PostgreSQL Flexible Server — Burstable B1ms
# ============================================================
Write-Host "[5/12] Creating PostgreSQL server '$DbServerName' (this takes ~3 min)..." -ForegroundColor Cyan
az postgres flexible-server create `
    --resource-group $ResourceGroup `
    --name           $DbServerName `
    --location       $Location `
    --admin-user     $DbAdminUser `
    --admin-password $DbAdminPassword `
    --sku-name       Standard_B1ms `
    --tier           Burstable `
    --storage-size   32 `
    --version        16 `
    --yes

# 0.0.0.0/0.0.0.0 is the documented special-case meaning "Allow Azure services only",
# not a wide-open internet rule
az postgres flexible-server firewall-rule create `
    --resource-group    $ResourceGroup `
    --name              $DbServerName `
    --rule-name         AllowAzureServices `
    --start-ip-address  0.0.0.0 `
    --end-ip-address    0.0.0.0

# Allow your current machine's IP for direct psql access / admin / debugging
$MyIp = (Invoke-RestMethod -Uri "https://ifconfig.me").Trim()
az postgres flexible-server firewall-rule create `
    --resource-group    $ResourceGroup `
    --name              $DbServerName `
    --rule-name         AllowMyIP `
    --start-ip-address  $MyIp `
    --end-ip-address    $MyIp

az postgres flexible-server db create `
    --resource-group $ResourceGroup `
    --server-name    $DbServerName `
    --database-name  $DbName

# ============================================================
# 6. Container Apps environment
# ============================================================
Write-Host "[6/12] Creating Container Apps environment '$ContainerAppsEnv'..." -ForegroundColor Cyan
az containerapp env create `
    --name           $ContainerAppsEnv `
    --resource-group $ResourceGroup `
    --location       $Location

# ============================================================
# 7. Build connection strings
# ============================================================
# Use the psycopg2 dialect prefix that the app's SQLAlchemy config expects
$DbConnString = "postgresql+psycopg2://${DbAdminUser}:${DbAdminPassword}@${DbServerName}.postgres.database.azure.com:5432/${DbName}?sslmode=require"

$StorageConnString = az storage account show-connection-string `
    --name           $StorageAccountName `
    --resource-group $ResourceGroup `
    --query          connectionString `
    --output         tsv

# ============================================================
# 8. Build + push backend image to GHCR
# ============================================================
Write-Host "[8/12] Building and pushing backend image..." -ForegroundColor Cyan
$BackendImage = "ghcr.io/$GithubUsername/ygt-backend:latest"

docker login ghcr.io -u $GithubUsername -p $GhcrPat
docker build -t $BackendImage "$RepoRoot\backend"
docker push $BackendImage

# ============================================================
# 9. Deploy backend container app
# ============================================================
Write-Host "[9/12] Deploying backend container app..." -ForegroundColor Cyan

az containerapp create `
    --name           $BackendAppName `
    --resource-group $ResourceGroup `
    --environment    $ContainerAppsEnv `
    --image          $BackendImage `
    --target-port    8000 `
    --ingress        external `
    --min-replicas   0 `
    --max-replicas   2 `
    --registry-server   "ghcr.io" `
    --registry-username $GithubUsername `
    --registry-password $GhcrPat `
    --env-vars `
        "DATABASE_URL=$DbConnString" `
        "SECRET_KEY=$SecretKey" `
        "CORS_ORIGINS=[`"*`"]"

# The storage connection string contains semicolons, which can confuse shell parsers.
# Store it as a Container Apps secret and reference it via secretref instead.
az containerapp secret set `
    --name           $BackendAppName `
    --resource-group $ResourceGroup `
    --secrets        "storage-conn-str=$StorageConnString"

az containerapp update `
    --name           $BackendAppName `
    --resource-group $ResourceGroup `
    --set-env-vars   "AZURE_STORAGE_CONNECTION_STRING=secretref:storage-conn-str"

$BackendFqdn = az containerapp show `
    --name           $BackendAppName `
    --resource-group $ResourceGroup `
    --query          "properties.configuration.ingress.fqdn" `
    --output         tsv

Write-Host "  Backend FQDN: $BackendFqdn" -ForegroundColor Green

# ============================================================
# 10. Build + push frontend image
#     NEXT_PUBLIC_* vars are baked into the bundle at build time — they MUST be
#     passed as --build-arg, not as Container Apps env vars at runtime
# ============================================================
Write-Host "[10/12] Building and pushing frontend image..." -ForegroundColor Cyan
$FrontendImage = "ghcr.io/$GithubUsername/ygt-frontend:latest"

docker build `
    --build-arg "NEXT_PUBLIC_API_URL=https://$BackendFqdn/api/v1" `
    -t $FrontendImage `
    "$RepoRoot\frontend"
docker push $FrontendImage

# ============================================================
# 11. Deploy frontend container app
# ============================================================
Write-Host "[11/12] Deploying frontend container app..." -ForegroundColor Cyan
az containerapp create `
    --name           $FrontendAppName `
    --resource-group $ResourceGroup `
    --environment    $ContainerAppsEnv `
    --image          $FrontendImage `
    --target-port    3000 `
    --ingress        external `
    --min-replicas   0 `
    --max-replicas   2 `
    --registry-server   "ghcr.io" `
    --registry-username $GithubUsername `
    --registry-password $GhcrPat

$FrontendFqdn = az containerapp show `
    --name           $FrontendAppName `
    --resource-group $ResourceGroup `
    --query          "properties.configuration.ingress.fqdn" `
    --output         tsv

# ============================================================
# 12. Lock down backend CORS to the actual frontend origin
# ============================================================
Write-Host "[12/12] Updating backend CORS to frontend origin..." -ForegroundColor Cyan
az containerapp update `
    --name           $BackendAppName `
    --resource-group $ResourceGroup `
    --set-env-vars `
        "CORS_ORIGINS=[`"https://$FrontendFqdn`"]" `
        "FRONTEND_URL=https://$FrontendFqdn"

# ============================================================
# Done
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "  Backend:   https://$BackendFqdn" -ForegroundColor Green
Write-Host "  Frontend:  https://$FrontendFqdn" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps for CI/CD (.github/workflows/deploy.yml):" -ForegroundColor Yellow
Write-Host "  1. Create an Azure AD App Registration and add a federated" -ForegroundColor Yellow
Write-Host "     credential for GitHub Actions OIDC (no stored passwords):" -ForegroundColor Yellow
Write-Host "     https://learn.microsoft.com/azure/developer/github/connect-from-azure-oidc" -ForegroundColor Yellow
Write-Host "  2. Assign the App Registration 'Contributor' on '$ResourceGroup'" -ForegroundColor Yellow
Write-Host "  3. Add these secrets to your GitHub repo:" -ForegroundColor Yellow
Write-Host "       AZURE_CLIENT_ID      (App Registration Application ID)" -ForegroundColor Yellow
Write-Host "       AZURE_TENANT_ID      (your Azure AD tenant ID)" -ForegroundColor Yellow
Write-Host "       AZURE_SUBSCRIPTION_ID" -ForegroundColor Yellow
Write-Host "  4. Push to main — the workflow handles all future deploys." -ForegroundColor Yellow
