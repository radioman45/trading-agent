# DART 키를 .env에서 읽어 현재 PowerShell 세션 + 사용자 영구 환경변수에 등록하고 검증한다.
# 사용법(trading-agent 디렉토리에서):  . .\scripts\load-dart-key.ps1
#   ※ 앞의 점(.)을 꼭 붙여 dot-source 해야 현재 세션에 환경변수가 남습니다.

$envFile = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $envFile)) { Write-Host "[오류] .env 없음: $envFile" -ForegroundColor Red; return }

$line = Get-Content $envFile | Where-Object { $_ -match '^\s*API_K_DART\s*=' } | Select-Object -First 1
if (-not $line) { Write-Host "[오류] .env에 API_K_DART 라인 없음" -ForegroundColor Red; return }

$key = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
if ([string]::IsNullOrWhiteSpace($key) -or $key -eq 'PASTE_YOUR_KEY_HERE') {
    Write-Host "[대기] .env의 API_K_DART가 아직 비어 있습니다. opendart.fss.or.kr에서 발급받은 키를 붙여넣으세요." -ForegroundColor Yellow
    return
}
if ($key.Length -ne 40) {
    Write-Host "[경고] 키 길이가 40자가 아닙니다(현재 $($key.Length)자). DART 키는 보통 40자 16진수입니다. 그래도 진행합니다." -ForegroundColor Yellow
}

# 현재 세션 + 사용자 영구 등록
$env:API_K_DART = $key
[Environment]::SetEnvironmentVariable("API_K_DART", $key, "User")
Write-Host "[적용] API_K_DART 등록 완료 (마스킹: $($key.Substring(0,6))…$($key.Substring($key.Length-4)))" -ForegroundColor Green

# 실호출 검증 — DART 기업개황 API로 삼성전자(00126380) 조회
try {
    $url = "https://opendart.fss.or.kr/api/company.json?crtfc_key=$key&corp_code=00126380"
    $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 15
    if ($resp.status -eq "000") {
        Write-Host "[검증 성공] DART 응답 정상 — 회사명: $($resp.corp_name) / 대표: $($resp.ceo_nm)" -ForegroundColor Green
    } else {
        Write-Host "[검증 실패] DART status=$($resp.status): $($resp.message)" -ForegroundColor Red
        Write-Host "  (010=등록되지 않은 키, 020=일일 한도 초과, 013=조회 데이터 없음 등)" -ForegroundColor DarkGray
    }
} catch {
    Write-Host "[검증 오류] API 호출 실패: $($_.Exception.Message)" -ForegroundColor Red
}
