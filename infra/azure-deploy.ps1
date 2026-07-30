# ============================================================
# YouGotTalent Azure Dev Deployment Script
#
# Prerequisites:
#   - Azure CLI installed (az --version)
#   - You've run `az login` yourself in a terminal and authenticated
#   - Docker images for backend/frontend already pushed to a registry
#     (see the PREREQUISITE section below before running steps 9-10)
#
# Run section by section rather than all at once the first time, so you
# can check each resource was created as expected before moving on.
# ============================================================

# ------------------------------------------------------------
# 1. Variables - EDIT THESE before running anything else
# ------------------------------------------------------------
$ResourceGroup      = "rg-ygt-dev"
$Location           = "eastus"                       # try eastus/westeurope if another region is restricted on your free account
$DbServerName       = "ygt-pg-dev"                    # must be globally unique
$DbAdminUser        = "ygtadmin"
$DbAdminPassword    = "ChangeMe123!ReplaceMe"          # strong password, don't commit this anywhere
$DbName             = "ygt"
$StorageAccountName = "ygtdevstorage001"               # globally unique, lowercase, 3-24 chars, no dashes
$ContainerAppsEnv   = "ygt-env"
$BackendAppName     = "ygt-backend"
$FrontendAppName    = "ygt-frontend"
$AlertEmail         = "you@example.com"

# ------------------------------------------------------------
# 2. Resource group - everything lives here so you can delete
#    the whole project in one command later if needed
# ------------------------------------------------------------
az group create --name $ResourceGroup --location $Location

# ------------------------------------------------------------
# 3. Budget alert - verify syntax with `az consumption budget create --help`
#    first; this command's arguments have shifted across API versions.
#    Portal path (Cost Management -> Budgets) is the reliable fallback.
# ------------------------------------------------------------
$StartDate = Get-Date -Format "yyyy-MM-01"
$Notifications = @"
{
  "Actual_GreaterThan_50_Percent": {"enabled": true, "operator": "GreaterThan", "threshold": 50, "contactEmails": ["$AlertEmail"], "thresholdType": "Actual"},
  "Actual_GreaterThan_90_Percent": {"enabled": true, "operator": "GreaterThan", "threshold": 90, "contactEmails": ["$AlertEmail"], "thresholdType": "Actual"}
}
"@

az consumption budget create `
  --budget-name "ygt-dev-budget" `
  --resource-group $ResourceGroup `
  --amount 180 `
  --category cost `
  --time-grain monthly `
  --start-date $StartDate `
  --end-date 2027-01-01 `
  --notifications $Notifications

# ------------------------------------------------------------
# 4. Storage account + blob container for talent media (images)
#    Standard/LRS/Hot - cheapest tier, within the free 5GB allowance
# ------------------------------------------------------------
az storage account create `
  --name $StorageAccountName `
  --resource-group $ResourceGroup `
  --location $Location `
  --sku Standard_LRS `
  --kind StorageV2 `
  --access-tier Hot

# --public-access blob makes individual blob URLs publicly readable (no SAS
# token needed) - matches how the app already stores plain media URLs
az storage container create `
  --account-name $StorageAccountName `
  --name talent-media `
  --auth-mode login `
  --public-access blob

# ------------------------------------------------------------
# 5. PostgreSQL Flexible Server - Burstable B1ms
# ------------------------------------------------------------
az postgres flexible-server create `
  --resource-group $ResourceGroup `
  --name $DbServerName `
  --location $Location `
  --admin-user $DbAdminUser `
  --admin-password $DbAdminPassword `
  --sku-name Standard_B1ms `
  --tier Burstable `
  --storage-size 32 `
  --version 16 `
  --yes

# Allow Azure services (Container Apps) to reach the DB - 0.0.0.0/0.0.0.0 is
# the documented special-case range meaning "allow Azure services", not a
# wide-open-to-the-internet rule
az postgres flexible-server firewall-rule create `
  --resource-group $ResourceGroup `
  --name $DbServerName `
  --rule-name AllowAzureServices `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0

# Allow your own machine's IP so you can psql/admin in directly
$MyIp = (Invoke-RestMethod -Uri "https://ifconfig.me/ip")
az postgres flexible-server firewall-rule create `
  --resource-group $ResourceGroup `
  --name $DbServerName `
  --rule-name AllowMyIP `
  --start-ip-address $MyIp `
  --end-ip-address $MyIp

az postgres flexible-server db create `
  --resource-group $ResourceGroup `
  --server-name $DbServerName `
  --database-name $DbName

# ------------------------------------------------------------
# 6. Container Apps environment
# ------------------------------------------------------------
az containerapp env create `
  --name $ContainerAppsEnv `
  --resource-group $ResourceGroup `
  --location $Location

# ------------------------------------------------------------
# 7. Build connection strings to pass into the apps
# ------------------------------------------------------------
$DbConnString = "postgresql://${DbAdminUser}:${DbAdminPassword}@${DbServerName}.postgres.database.azure.com:5432/${DbName}?sslmode=require"

$StorageConnString = az storage account show-connection-string `
  --name $StorageAccountName `
  --resource-group $ResourceGroup `
  --query connectionString -o tsv

# ------------------------------------------------------------
# 8. PREREQUISITE: build + push your images to a free registry first.
#    Container Apps needs a real image to deploy - steps 9-10 will fail
#    if ghcr.io/<you>/<repo> doesn't exist yet. Run from your repo root:
#
#    docker build -t ghcr.io/<github-username>/ygt-backend:latest ./backend
#    docker build -t ghcr.io/<github-username>/ygt-frontend:latest ./frontend
#    docker login ghcr.io -u <github-username>   # password: a GitHub PAT with write:packages scope
#    docker push ghcr.io/<github-username>/ygt-backend:latest
#    docker push ghcr.io/<github-username>/ygt-frontend:latest
#
#    If the GHCR repo is private, also add --registry-server ghcr.io
#    --registry-username <github-username> --registry-password <PAT>
#    to the containerapp create calls below.
# ------------------------------------------------------------

# ------------------------------------------------------------
# 9. Deploy backend
# ------------------------------------------------------------
az containerapp create `
  --name $BackendAppName `
  --resource-group $ResourceGroup `
  --environment $ContainerAppsEnv `
  --image "ghcr.io/<github-username>/ygt-backend:latest" `
  --target-port 8000 `
  --ingress external `
  --min-replicas 0 `
  --max-replicas 2 `
  --env-vars "DATABASE_URL=$DbConnString" "AZURE_STORAGE_CONNECTION_STRING=$StorageConnString"

$BackendFqdn = az containerapp show `
  --name $BackendAppName `
  --resource-group $ResourceGroup `
  --query properties.configuration.ingress.fqdn -o tsv

# ------------------------------------------------------------
# 10. Deploy frontend, pointed at the backend's auto-generated URL
# ------------------------------------------------------------
az containerapp create `
  --name $FrontendAppName `
  --resource-group $ResourceGroup `
  --environment $ContainerAppsEnv `
  --image "ghcr.io/<github-username>/ygt-frontend:latest" `
  --target-port 3000 `
  --ingress external `
  --min-replicas 0 `
  --max-replicas 2 `
  --env-vars "NEXT_PUBLIC_API_URL=https://$BackendFqdn/api/v1"

$FrontendFqdn = az containerapp show --name $FrontendAppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv
Write-Host "Backend:  https://$BackendFqdn"
Write-Host "Frontend: https://$FrontendFqdn"

# ------------------------------------------------------------
# Teardown (when you're done / want to stop all charges):
#   az group delete --name $ResourceGroup --yes --no-wait
# ------------------------------------------------------------
