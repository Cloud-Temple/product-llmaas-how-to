<#
.SYNOPSIS
    Teste l'API LLM sur plusieurs modèles avec des options avancées et des statistiques détaillées.

.DESCRIPTION
    Ce script permet de tester l'API LLM en envoyant une requête à plusieurs modèles
    et en comparant leurs réponses. Il offre diverses options de personnalisation
    comme le choix des modèles, le nombre de passes, le mode debug, etc.
    Il lit la configuration (endpoint API, token) depuis un fichier config.json.
    Il récupère dynamiquement la liste des modèles disponibles depuis l'API.
    Il affiche les statistiques détaillées pour chaque passe et un tableau récapitulatif coloré.

.PARAMETER Models
    Liste des ID de modèles à tester, séparés par des virgules. 
    Si omis, tous les modèles disponibles seront testés.

.PARAMETER Prompt
    Le prompt à envoyer aux modèles. 
    Par défaut: "Ecris-moi un mot de plus de 10 lettres au hasard sans fioriture ?"

.PARAMETER Passes
    Nombre de passes (requêtes) à effectuer pour chaque modèle. 
    La priorité est : Paramètre CLI > config.json > 1 (défaut script).

.PARAMETER Debug
    Active le mode debug pour afficher des informations détaillées sur les requêtes, 
    les réponses (payloads JSON formatés) et les erreurs.

.PARAMETER ConfigFile
    Chemin relatif vers le fichier de configuration JSON. 
    Par défaut: "./config.json".

.PARAMETER Temperature
    Température à utiliser pour les requêtes (contrôle la créativité). 
    Priorité : Paramètre CLI > config.json > 0.7 (défaut script).

.PARAMETER MaxTokens
    Nombre maximum de tokens à générer dans la réponse. 
    Priorité : Paramètre CLI > config.json > 1024 (défaut script).

.EXAMPLE
    .\test_api_models.ps1
    Teste tous les modèles disponibles, nombre de passes selon config ou 1, paramètres de config.json.

.EXAMPLE
    .\test_api_models.ps1 -Models "cogito,granite3.3" -Passes 5
    Teste uniquement les modèles "cogito" et "granite3.3" avec 5 passes pour chacun.

.EXAMPLE
    .\test_api_models.ps1 -Prompt "Quelle est la capitale de la France ?" -Debug
    Teste tous les modèles (passes selon config ou 1), prompt personnalisé, mode debug activé.

.NOTES
    Auteur: Cline
    Date: 2025-05-31
    Assurez-vous que le fichier config.json existe et contient au minimum {"api": {"endpoint": "URL_API", "token": "VOTRE_TOKEN"}}.
    Les statistiques de tokens et le modèle utilisé dépendent de leur présence dans la réponse de l'API.
#>

param (
    [string]$Models = "",
    [string]$Prompt = "Ecris-moi un mot de plus de 10 lettres au hasard sans fioriture ?",
    [int]$Passes, 
    [switch]$Debug,
    [string]$ConfigFile = "./config.json",
    [double]$Temperature = -1.0, 
    [int]$MaxTokens = -1 
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

#region Fonctions d'affichage et utilitaires
function Write-ColorOutput {
    param ([string]$Text, [string]$ForegroundColor = "White", [switch]$NoNewLine)
    $originalColor = $host.UI.RawUI.ForegroundColor
    try {
        $host.UI.RawUI.ForegroundColor = $ForegroundColor
        if ($NoNewLine) { Write-Host $Text -NoNewline } else { Write-Host $Text }
    }
    finally { $host.UI.RawUI.ForegroundColor = $originalColor }
}

function Write-DebugInfo {
    param ([string]$Message, [string]$Title = "[DEBUG]")
    if ($Debug) { Write-ColorOutput "$Title $Message" -ForegroundColor "Cyan" }
}

function Write-Error {
    param ([string]$Message)
    Write-ColorOutput "[ERREUR] $Message" -ForegroundColor "Red"
}

function Write-Success {
    param ([string]$Message)
    Write-ColorOutput "[SUCCÈS] $Message" -ForegroundColor "Green"
}

function Write-Info {
    param ([string]$Message)
    Write-ColorOutput "[INFO] $Message" -ForegroundColor "Yellow"
}

function Format-JsonForDisplay {
    param ([string]$JsonString)
    try {
        return ($JsonString | ConvertFrom-Json -ErrorAction Stop | ConvertTo-Json -Depth 100)
    } catch {
        Write-DebugInfo "Impossible de formater le JSON pour l'affichage: $($_.Exception.Message)"
        return $JsonString 
    }
}

function Format-ElapsedTime {
    param ([Parameter(Mandatory=$true)][TimeSpan]$TimeSpan)
    if ($TimeSpan.TotalSeconds -lt 1) { return "$([math]::Round($TimeSpan.TotalMilliseconds, 0)) ms" }
    if ($TimeSpan.TotalMinutes -lt 1) { return "$([math]::Round($TimeSpan.TotalSeconds, 2)) s" }
    return "$([math]::Round($TimeSpan.TotalMinutes, 2)) min"
}

function Get-FormattedSize {
    param ([Parameter(Mandatory=$true)][string]$Text)
    if (-not $Text) { return "0 octets" }
    $bytes = [System.Text.Encoding]::UTF8.GetByteCount($Text)
    if ($bytes -lt 1024) { return "$bytes octets" }
    if ($bytes -lt (1024 * 1024)) { return "$([math]::Round($bytes / 1024, 2)) Ko" }
    return "$([math]::Round($bytes / (1024 * 1024), 2)) Mo"
}
#endregion

#region Chargement de la configuration
$ApiEndpoint = $null
$ApiToken = $null
$ScriptDefaultPasses = 1
$ScriptDefaultTemperature = 0.7
$ScriptDefaultMaxTokens = 1024
$ScriptDefaultTimeout = 30

$EffectivePasses = $ScriptDefaultPasses
$EffectiveTemperature = $ScriptDefaultTemperature
$EffectiveMaxTokens = $ScriptDefaultMaxTokens
$TimeoutSec = $ScriptDefaultTimeout

try {
    $configPath = Join-Path -Path $PSScriptRoot -ChildPath $ConfigFile
    Write-DebugInfo "Chargement de la configuration depuis: $configPath"
    if (-not (Test-Path $configPath)) { throw "Fichier de configuration non trouvé: $configPath" }
    
    $config = (Get-Content -Path $configPath -Raw -Encoding UTF8) | ConvertFrom-Json
    
    if (-not ($config.api.endpoint -and $config.api.token)) {
        throw "Configuration API incomplète. 'api.endpoint' et 'api.token' sont requis."
    }
    $ApiEndpoint = $config.api.endpoint
    $ApiToken = $config.api.token
    
    if ($config.defaults) {
        if ($config.defaults.PSObject.Properties.Name -contains 'passes') { $EffectivePasses = $config.defaults.passes }
        if ($config.defaults.PSObject.Properties.Name -contains 'temperature') { $EffectiveTemperature = $config.defaults.temperature }
        if ($config.defaults.PSObject.Properties.Name -contains 'max_tokens') { $EffectiveMaxTokens = $config.defaults.max_tokens }
        if ($config.defaults.PSObject.Properties.Name -contains 'timeout') { $TimeoutSec = $config.defaults.timeout }
    }

    if ($PSBoundParameters.ContainsKey('Passes')) { $EffectivePasses = $Passes }
    if ($PSBoundParameters.ContainsKey('Temperature')) { $EffectiveTemperature = $Temperature }
    if ($PSBoundParameters.ContainsKey('MaxTokens')) { $EffectiveMaxTokens = $MaxTokens }

    Write-DebugInfo "Configuration finale: Endpoint='$ApiEndpoint', Passes=$EffectivePasses, Temp=$EffectiveTemperature, MaxTokens=$EffectiveMaxTokens, Timeout=$TimeoutSec"
} catch {
    Write-Error "Erreur config '$ConfigFile': $($_.Exception.Message)"; exit 1
}
#endregion

#region Récupération des modèles disponibles
function Get-AvailableModels {
    param([string]$Endpoint, [string]$Token, [int]$Timeout)
    Write-Info "Récupération de la liste des modèles disponibles..."
    $headers = @{"accept"="application/json"; "Authorization"="Bearer $Token"}
    $modelsUri = "$Endpoint/models"
    Write-DebugInfo "Requête GET vers $modelsUri"
    try {
        $response = Invoke-WebRequest -Uri $modelsUri -Method Get -Headers $headers -ErrorAction Stop -TimeoutSec $Timeout
        $modelsData = $response.Content | ConvertFrom-Json
        if (-not $modelsData.data) { throw "Format de réponse API inattendu (propriété 'data' manquante)." }
        Write-Success "Liste des modèles récupérée ($($modelsData.data.Count) modèles)"
        if ($Debug) { Write-DebugInfo "Modèles: $(($modelsData.data | ForEach-Object {$_.id}) -join ', ')" }
        return $modelsData.data
    } catch {
        Write-Error "Erreur récupération modèles: $($_.Exception.Message)"
        if ($Debug -and $_.Exception.Response) {
            $status = "$($_.Exception.Response.StatusCode.Value__) $($_.Exception.Response.StatusDescription)"
            Write-DebugInfo "Status: $status"
            try {
                $responseStream = $_.Exception.Response.GetResponseStream()
                $streamReader = New-Object System.IO.StreamReader($responseStream, [System.Text.Encoding]::UTF8)
                $errorResponseContent = $streamReader.ReadToEnd()
                $streamReader.Close()
                $responseStream.Close()
                Write-DebugInfo "[PAYLOAD ERREUR REÇU]" -Title ""
                Write-DebugInfo (Format-JsonForDisplay -JsonString $errorResponseContent) -Title ""
            } catch { Write-DebugInfo "Impossible de lire/formater le corps de l'erreur."}
        }
        return $null
    }
}
#endregion

#region Exécution des tests
function Invoke-ModelTest {
    param (
        [PSCustomObject]$ModelObject, [string]$UserPrompt, [int]$PassCount, 
        [double]$Temp, [int]$MaxTokenCount, [string]$Endpoint, 
        [string]$Token, [int]$Timeout
    )
    $modelResults = [PSCustomObject]@{
        ModelId = $ModelObject.id; DisplayName = $ModelObject.id; Responses = [System.Collections.Generic.List[object]]::new();
        TotalTime = [TimeSpan]::Zero; SuccessCount = 0; ErrorCount = 0; TotalPromptTokens = 0;
        TotalCompletionTokens = 0; TotalReasoningTokens = 0; TotalTokensPerSecond = [System.Collections.Generic.List[double]]::new()
    }
    if ($ModelObject.PSObject.Properties.Name -contains 'aliases' -and $ModelObject.aliases -is [array] -and $ModelObject.aliases.Count -gt 0) {
        $modelResults.DisplayName = $ModelObject.aliases[0]
    }
    
    Write-ColorOutput "`n=======================================" -ForegroundColor "Magenta"
    Write-ColorOutput "Test du modèle: $($modelResults.DisplayName) (ID API: $($modelResults.ModelId))" -ForegroundColor "Magenta"
    Write-ColorOutput "=======================================" -ForegroundColor "Magenta"
    
    $headers = @{"accept"="application/json";"Authorization"="Bearer $Token";"Content-Type"="application/json; charset=utf-8"}
    $bodyObject = @{
        "model"=$modelResults.ModelId; "messages"=@(@{"role"="user";"content"=$UserPrompt}); "stream"=$false;
        "temperature"=$Temp; "top_p"=1; "n"=1; "max_tokens"=$MaxTokenCount; "user"="test-script-powershell-user"
    }
    $bodyJson = $bodyObject | ConvertTo-Json -Compress -Depth 5
    if ($Debug) {
        Write-DebugInfo "[PAYLOAD ENVOYÉ]" -Title ""
        Write-DebugInfo (Format-JsonForDisplay -JsonString $bodyJson) -Title ""
    }
    
    for ($i = 1; $i -le $PassCount; $i++) {
        Write-ColorOutput "Passe $i / $PassCount pour $($modelResults.DisplayName): " -ForegroundColor "Blue" -NoNewLine
        $startTime = Get-Date
        $responseInfo = @{ Result=""; Time=[TimeSpan]::Zero; Status="Error"; Size="N/A"; PromptTokens=0; CompletionTokens=0; ReasoningTokens=0; ModelUsed="N/A"; TokensPerSecond=0.0; RequestId="N/A"; BackendInfo="N/A" }
        try { 
            $response = Invoke-WebRequest -Uri "$Endpoint/chat/completions" -Method Post -Headers $headers -Body $bodyJson -ErrorAction Stop -TimeoutSec $Timeout -ContentType "application/json; charset=utf-8"
            $endTime = Get-Date; $elapsed = $endTime - $startTime
            $modelResults.TotalTime += $elapsed; $modelResults.SuccessCount++; $responseInfo.Time = $elapsed; $responseInfo.Status = "Success"
            $responseData = $response.Content | ConvertFrom-Json
            if ($Debug) { Write-DebugInfo "[PAYLOAD REÇU (Succès)]" -Title ""; Write-DebugInfo (Format-JsonForDisplay -JsonString $response.Content) -Title "" }
            if ($response.Headers.ContainsKey("x-request-id")) { $responseInfo.RequestId = $response.Headers["x-request-id"] }
            if ($responseData.choices[0].message.content) { $responseInfo.Result = $responseData.choices[0].message.content; $responseInfo.Size = Get-FormattedSize -Text $responseInfo.Result }
            if ($responseData.model) { $responseInfo.ModelUsed = $responseData.model }
            if ($responseData.usage) {
                if ($responseData.usage.PSObject.Properties.Name -contains 'prompt_tokens' -and $responseData.usage.prompt_tokens -ne $null) {
                    $responseInfo.PromptTokens = $responseData.usage.prompt_tokens
                } else {
                    $responseInfo.PromptTokens = 0
                }
                if ($responseData.usage.PSObject.Properties.Name -contains 'completion_tokens' -and $responseData.usage.completion_tokens -ne $null) {
                    $responseInfo.CompletionTokens = $responseData.usage.completion_tokens
                } else {
                    $responseInfo.CompletionTokens = 0
                }
                if ($responseData.usage.PSObject.Properties.Name -contains 'reasoning_tokens' -and $responseData.usage.reasoning_tokens -ne $null) {
                    $responseInfo.ReasoningTokens = $responseData.usage.reasoning_tokens
                } else {
                    $responseInfo.ReasoningTokens = 0
                }
                
                $modelResults.TotalPromptTokens += $responseInfo.PromptTokens
                $modelResults.TotalCompletionTokens += $responseInfo.CompletionTokens
                $modelResults.TotalReasoningTokens += $responseInfo.ReasoningTokens
                if ($responseInfo.CompletionTokens -gt 0 -and $elapsed.TotalSeconds -gt 0) {
                    $responseInfo.TokensPerSecond = [math]::Round($responseInfo.CompletionTokens / $elapsed.TotalSeconds, 2)
                    $modelResults.TotalTokensPerSecond.Add($responseInfo.TokensPerSecond)
                }
            }
            if ($responseData.backend) {
                $responseInfo.BackendInfo = "Machine: $($responseData.backend.machine_name), Moteur: $($responseData.backend.engine_type)"
            }
            Write-ColorOutput "OK" -ForegroundColor "Green"
            Write-ColorOutput "  Réponse: $($responseInfo.Result)" -ForegroundColor "White"
            Write-ColorOutput "  Temps: $(Format-ElapsedTime -TimeSpan $elapsed) | Taille: $($responseInfo.Size) | Modèle API: $($responseInfo.ModelUsed)" -ForegroundColor "Gray"
            Write-ColorOutput "  Tokens: Prompt=$($responseInfo.PromptTokens), Complétion=$($responseInfo.CompletionTokens), Raisonnement=$($responseInfo.ReasoningTokens) | Vitesse: $($responseInfo.TokensPerSecond) toks/s" -ForegroundColor "Gray"
            Write-ColorOutput "  Req ID: $($responseInfo.RequestId) | Backend: $($responseInfo.BackendInfo)" -ForegroundColor "Gray"
        } catch {
            $endTime = Get-Date; $elapsed = $endTime - $startTime
            $modelResults.TotalTime += $elapsed; $modelResults.ErrorCount++; $responseInfo.Time = $elapsed
            $errorMessage = if ($_.Exception.Response) { "Erreur $($_.Exception.Response.StatusCode.Value__) $($_.Exception.Response.StatusDescription)" } else { "Erreur Script/Réseau: $($_.Exception.Message)"}
            if ($Debug -and $_.Exception.Response) {
                Write-DebugInfo "[PAYLOAD ERREUR REÇU]" -Title ""
                try { 
                    $responseStream = $_.Exception.Response.GetResponseStream()
                    $streamReader = New-Object System.IO.StreamReader($responseStream, [System.Text.Encoding]::UTF8)
                    $errorContent = $streamReader.ReadToEnd()
                    $streamReader.Close(); $responseStream.Close()
                    Write-DebugInfo (Format-JsonForDisplay -JsonString $errorContent) -Title ""
                    $errorJson = $errorContent | ConvertFrom-Json -ErrorAction SilentlyContinue
                    if ($errorJson -and $errorJson.PSObject.Properties.Name -contains 'detail') { $errorMessage += " - $($errorJson.detail)"}
                } catch { Write-DebugInfo "Impossible de lire/formater le corps de l'erreur."}
            }
            $responseInfo.Result = $errorMessage
            Write-ColorOutput "ÉCHEC" -ForegroundColor "Red"; Write-ColorOutput "  Erreur: $errorMessage" -ForegroundColor "Red"
            Write-ColorOutput "  Temps: $(Format-ElapsedTime -TimeSpan $elapsed)" -ForegroundColor "Gray"
        }
        $modelResults.Responses.Add($responseInfo)
    } 
    return $modelResults
}
#endregion

#region Affichage du résumé
function Show-ResultsSummary {
    param ([array]$Results)
    Write-ColorOutput "`n==================================================================================================" -ForegroundColor "Magenta"
    Write-ColorOutput "                                     TABLEAU RÉCAPITULATIF                                      " -ForegroundColor "Magenta"
    Write-ColorOutput "==================================================================================================" -ForegroundColor "Magenta"
    $tableData = foreach ($result in $Results) {
        $totalRequests = $result.SuccessCount + $result.ErrorCount
        $avgTimeMs = if ($totalRequests -gt 0) { [math]::Round($result.TotalTime.TotalMilliseconds / $totalRequests, 0) } else { 0 }
        $avgPromptTokens = if ($result.SuccessCount -gt 0) { [math]::Round($result.TotalPromptTokens / $result.SuccessCount, 0) } else { 0 }
        $avgCompletionTokens = if ($result.SuccessCount -gt 0) { [math]::Round($result.TotalCompletionTokens / $result.SuccessCount, 0) } else { 0 }
        $avgReasoningTokens = if ($result.SuccessCount -gt 0) { [math]::Round($result.TotalReasoningTokens / $result.SuccessCount, 0) } else { 0 }
        $avgTokensPerSecond = if ($result.TotalTokensPerSecond.Count -gt 0) { [math]::Round(($result.TotalTokensPerSecond | Measure-Object -Sum).Sum / $result.TotalTokensPerSecond.Count, 2) } else { 0 }
        [PSCustomObject]@{ Modèle=$result.DisplayName; Succès=$result.SuccessCount; Erreurs=$result.ErrorCount; "Tps Moyen (ms)"=$avgTimeMs; "Tps Total"=(Format-ElapsedTime -TimeSpan $result.TotalTime); "Prompt Tok (moy)"=$avgPromptTokens; "Compl Tok (moy)"=$avgCompletionTokens; "Reas Tok (moy)"=$avgReasoningTokens; "Tok/s (moy)"=$avgTokensPerSecond }
    }
    if ($tableData.Count -gt 0) { 
        # Affichage direct du tableau récapitulatif
        $tableData | Format-Table -AutoSize 
    } 
    else { Write-Info "Aucune donnée à afficher dans le résumé." }
    Write-ColorOutput "==================================================================================================" -ForegroundColor "Magenta"
}
#endregion

#region Programme principal
Write-ColorOutput "`n==========================================================" -ForegroundColor "Green"
Write-ColorOutput "      TEST DES MODÈLES LLM - COMPARAISON DE RÉPONSES      " -ForegroundColor "Green"
Write-ColorOutput "==========================================================" -ForegroundColor "Green"
Write-ColorOutput "Prompt: $Prompt" -ForegroundColor "Yellow"
Write-ColorOutput "Passes par modèle: $EffectivePasses" -ForegroundColor "Yellow"
Write-ColorOutput "Température: $EffectiveTemperature" -ForegroundColor "Yellow"
Write-ColorOutput "Max Tokens: $EffectiveMaxTokens" -ForegroundColor "Yellow"
if ($Debug) { Write-ColorOutput "Mode Debug: ACTIVÉ" -ForegroundColor "Cyan" }
Write-ColorOutput "==========================================================" -ForegroundColor "Green"

$availableModels = Get-AvailableModels -Endpoint $ApiEndpoint -Token $ApiToken -Timeout $TimeoutSec
if (-not $availableModels) { Write-Error "Arrêt du script."; exit 1 }

$modelsToTest = [System.Collections.Generic.List[object]]::new()
if ($Models) {
    $requestedModels = $Models -split ',' | ForEach-Object { $_.Trim() }
    foreach ($modelId in $requestedModels) {
        $foundModel = $availableModels | Where-Object { $_.id.Equals($modelId, [System.StringComparison]::OrdinalIgnoreCase) }
        if ($foundModel) { $modelsToTest.Add($foundModel); Write-DebugInfo "Modèle '$($foundModel.id)' ajouté pour test." }
        else { Write-Error "Modèle demandé '$modelId' non trouvé." }
    }
    if ($modelsToTest.Count -eq 0) { Write-Error "Aucun des modèles demandés n'a été trouvé. Arrêt."; exit 1 }
} else {
    $modelsToTest.AddRange($availableModels)
    Write-Info "Test de tous les $($modelsToTest.Count) modèles disponibles."
}

if ($modelsToTest.Count -gt 0) {
    Write-ColorOutput "`n----------------------------------------------------------" -ForegroundColor "Yellow"
    Write-ColorOutput "MODÈLES SÉLECTIONNÉS POUR LE TEST:" -ForegroundColor "Yellow"
    Write-ColorOutput "----------------------------------------------------------" -ForegroundColor "Yellow"
    
    $modelsForTableDisplay = [System.Collections.Generic.List[object]]::new()
    # Write-DebugInfo "Début de la construction de la liste des modèles pour affichage. Nombre d'items dans modelsToTest: $($modelsToTest.Count)" # Nettoyé

    foreach ($modelItem in $modelsToTest) {
        # Write-DebugInfo "Vérification du modèle $($modelItem.id) pour affichage..." # Nettoyé

        $skipModel = $false
        if (-not ($modelItem -and $modelItem.PSObject.Properties.Name -contains 'id' -and -not [string]::IsNullOrWhiteSpace($modelItem.id))) {
            Write-DebugInfo "Modèle ignoré pour l'affichage (ID manquant/nul/vide): $(ConvertTo-Json $modelItem -Depth 1 -Compress -ErrorAction SilentlyContinue)"
            $skipModel = $true
        }
        if ($skipModel) { continue }

        $displayName = $modelItem.id 
        if ($modelItem.aliases -is [array] -and $modelItem.aliases.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($modelItem.aliases[0])) {
            $displayName = $modelItem.aliases[0]
        }
        $modelsForTableDisplay.Add([PSCustomObject]@{"ID Modèle (API)"=$modelItem.id; "Nom d'Affichage"=$displayName})
    } 
    
    Write-DebugInfo "Construction de la liste pour affichage terminée. Items: $($modelsForTableDisplay.Count)"

    if ($modelsForTableDisplay.Count -gt 0) {
        $modelsForTableDisplay | Format-Table -Property "ID Modèle (API)", "Nom d'Affichage" -AutoSize 
    } else {
        Write-Info "Aucun modèle valide à afficher dans le tableau (count: $($modelsForTableDisplay.Count))."
    }
    Write-ColorOutput "----------------------------------------------------------" -ForegroundColor "Yellow"
} else {
    Write-Error "Aucun modèle sélectionné pour le test."; exit 1
}

$allResults = [System.Collections.Generic.List[object]]::new()
foreach ($modelEntry in $modelsToTest) {
    $modelResult = Invoke-ModelTest -ModelObject $modelEntry -UserPrompt $Prompt -PassCount $EffectivePasses -Temp $EffectiveTemperature -MaxTokenCount $EffectiveMaxTokens -Endpoint $ApiEndpoint -Token $ApiToken -Timeout $TimeoutSec
    $allResults.Add($modelResult)
}

if ($allResults.Count -gt 0) { Show-ResultsSummary -Results $allResults } 
else { Write-Info "Aucun test n'a été exécuté." }

Write-ColorOutput "`nTests terminés!" -ForegroundColor "Green"
#endregion
