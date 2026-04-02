# Azure Deployment Script - Energy Dashboard
# This script automates the Azure Portal steps using Azure CLI
# Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# =============================================================================
# VARIABLES - UPDATE THESE BEFORE RUNNING
# =============================================================================

$subscriptionId = "YOUR_SUBSCRIPTION_ID"  # Get from Azure Portal
$resourceGroupName = "energy-dashboard-rg"
$location = "eastus"  # Change to your preferred region

$backendServiceName = "energy-dashboard-api"
$frontendServiceName = "energy-dashboard-app"
$appServicePlanName = "energy-dashboard-plan"

# SharePoint credentials (optional)
$sharepointSiteUrl = "https://yourcompany.sharepoint.com/sites/energy"
$sharepointClientId = "your-client-id"
$sharepointClientSecret = "your-client-secret"

# Email credentials (optional)
$smtpHost = "smtp.gmail.com"
$smtpUsername = "your-email@gmail.com"
$smtpPassword = "your-app-password"

# =============================================================================
# SCRIPT STARTS HERE
# =============================================================================

Write-Host "======================================"
Write-Host "Energy Dashboard - Azure Deployment"
Write-Host "======================================"
Write-Host ""

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI..."
try {
    az --version > $null
    Write-Host "✓ Azure CLI found" -ForegroundColor Green
} catch {
    Write-Host "✗ Azure CLI not found. Install from: https://docs.microsoft.com/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Logging in to Azure..."
az login --subscription $subscriptionId

# =============================================================================
# STEP 1: Create Resource Group
# =============================================================================

Write-Host ""
Write-Host "Step 1/5: Creating Resource Group..."
az group create `
    --name $resourceGroupName `
    --location $location

Write-Host "✓ Resource Group created" -ForegroundColor Green

# =============================================================================
# STEP 2: Create App Service Plan
# =============================================================================

Write-Host ""
Write-Host "Step 2/5: Creating App Service Plan..."
az appservice plan create `
    --name $appServicePlanName `
    --resource-group $resourceGroupName `
    --sku F1 `
    --is-linux

Write-Host "✓ App Service Plan created" -ForegroundColor Green

# =============================================================================
# STEP 3: Create Backend App Service (Python)
# =============================================================================

Write-Host ""
Write-Host "Step 3/5: Creating Backend App Service..."
az webapp create `
    --resource-group $resourceGroupName `
    --plan $appServicePlanName `
    --name $backendServiceName `
    --runtime "PYTHON|3.11"

Write-Host "✓ Backend App Service created" -ForegroundColor Green

# Configure Backend Application Settings
Write-Host "Configuring Backend settings..."
az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $backendServiceName `
    --settings `
    API_HOST="0.0.0.0" `
    API_PORT="8000" `
    APP_ENV="production" `
    DEBUG="false" `
    API_RELOAD="false" `
    SHAREPOINT_SITE_URL=$sharepointSiteUrl `
    SHAREPOINT_CLIENT_ID=$sharepointClientId `
    SHAREPOINT_CLIENT_SECRET=$sharepointClientSecret `
    SMTP_HOST=$smtpHost `
    SMTP_PORT="587" `
    SMTP_USERNAME=$smtpUsername `
    SMTP_PASSWORD=$smtpPassword

Write-Host "✓ Backend settings configured" -ForegroundColor Green

# =============================================================================
# STEP 4: Create Frontend App Service (Node.js)
# =============================================================================

Write-Host ""
Write-Host "Step 4/5: Creating Frontend App Service..."
az webapp create `
    --resource-group $resourceGroupName `
    --plan $appServicePlanName `
    --name $frontendServiceName `
    --runtime "NODE|18-lts"

Write-Host "✓ Frontend App Service created" -ForegroundColor Green

# Configure Frontend Application Settings
Write-Host "Configuring Frontend settings..."
$backendUrl = "https://$backendServiceName.azurewebsites.net"

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $frontendServiceName `
    --settings `
    VITE_API_BASE_URL=$backendUrl `
    NODE_ENV="production"

Write-Host "✓ Frontend settings configured" -ForegroundColor Green

# =============================================================================
# STEP 5: Display Service URLs
# =============================================================================

Write-Host ""
Write-Host "Step 5/5: Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "======================================"
Write-Host "Your Services are Ready:"
Write-Host "======================================"
Write-Host ""
Write-Host "Backend API:"
Write-Host "  URL: https://$backendServiceName.azurewebsites.net" -ForegroundColor Cyan
Write-Host "  Docs: https://$backendServiceName.azurewebsites.net/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend App:"
Write-Host "  URL: https://$frontendServiceName.azurewebsites.net" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resource Group: $resourceGroupName" -ForegroundColor Yellow
Write-Host "Location: $location" -ForegroundColor Yellow
Write-Host ""

# =============================================================================
# NEXT STEPS
# =============================================================================

Write-Host "Next Steps:"
Write-Host "1. Deploy code to your services"
Write-Host "   - Option A: Use GitHub Actions (recommended)"
Write-Host "   - Option B: Upload ZIP files via Kudu"
Write-Host ""
Write-Host "2. Monitor deployments:"
Write-Host "   az webapp deployment log show --name $backendServiceName --resource-group $resourceGroupName"
Write-Host ""
Write-Host "3. View live logs:"
Write-Host "   az webapp log tail --name $backendServiceName --resource-group $resourceGroupName"
Write-Host ""
Write-Host "4. Configure GitHub Actions (optional):"
Write-Host "   az webapp deployment github-actions add --repo YOUR_GITHUB_REPO --branch main --name $backendServiceName --resource-group $resourceGroupName"
Write-Host ""

Write-Host ""
Write-Host "✓ Azure deployment script completed!" -ForegroundColor Green
Write-Host ""
Write-Host "For detailed setup, see AZURE_DEPLOYMENT_GUIDE.md"
