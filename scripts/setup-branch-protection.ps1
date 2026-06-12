<#
.SYNOPSIS
    Applies the 'protect-main' branch ruleset to a GitHub repository.

.DESCRIPTION
    Creates a repository ruleset that blocks direct pushes to main:
    - pull request required, 2 approving reviews, stale reviews dismissed
    - required status checks: tests (CI), security-scan (Bandit), Analyze (python) (CodeQL)
    - force pushes and branch deletion blocked

    Requires $env:GITHUB_TOKEN with repository "Administration: write" permission
    (fine-grained token) or the classic "repo" scope.

.EXAMPLE
    $env:GITHUB_TOKEN = '<token>'
    .\scripts\setup-branch-protection.ps1 -Owner wing-csi -Repo AIFlowTesting
#>
param(
    [string]$Owner = "wing-csi",
    [string]$Repo = "AIFlowTesting"
)

$ErrorActionPreference = "Stop"

if (-not $env:GITHUB_TOKEN) {
    throw "GITHUB_TOKEN is not set. Create a token at https://github.com/settings/tokens with repository Administration write access, then run: `$env:GITHUB_TOKEN = '<token>'"
}

$rulesetPath = Join-Path $PSScriptRoot "..\.github\ruleset-main.json"
if (-not (Test-Path $rulesetPath)) {
    throw "Ruleset definition not found at $rulesetPath"
}
$body = Get-Content $rulesetPath -Raw

$headers = @{
    Authorization          = "Bearer $($env:GITHUB_TOKEN)"
    Accept                 = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

try {
    $response = Invoke-RestMethod -Method Post `
        -Uri "https://api.github.com/repos/$Owner/$Repo/rulesets" `
        -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "Created ruleset '$($response.name)' (id $($response.id)) on $Owner/$Repo."
    Write-Host "Verify at: https://github.com/$Owner/$Repo/settings/rules"
}
catch {
    $detail = $_.ErrorDetails.Message
    if ($detail) { Write-Host "GitHub API error: $detail" }
    throw
}
