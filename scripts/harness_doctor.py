# -*- coding: utf-8 -*-
"""harness doctor — 기계적 검증 레이어 (2026-07-04, codex 리뷰 R3 반영).

LLM 팩트체커(Phase 1.6 등)는 유용하지만 마지막 방어선이 되면 안 된다.
결정적(deterministic)으로 검사 가능한 불변조건은 이 스크립트가 강제한다:

  1. 필수 산출물 존재         — 하네스별 required artifact matrix
  2. 스냅샷 필드 존재         — as_of / market_session / price.source
  3. 산술 정합               — 시총 = 가격 × 주식수, 등락률 vs 레벨
  4. 최종 결정 ↔ 게이트 모순  — ⛔치명 지적 존재 + 일반 APPROVE
  5. 검증·포트폴리오 모드     — holdings 비었는데 PORTFOLIO_AWARE 주장 금지 등
  6. 공시 경계               — 매매 판단 언어 휴리스틱 (filings 하네스)

등급 의미:
  FAIL = 불변조건 위반 — 오케스트레이터가 정정 루프(생산자 1회 재호출·라벨 정정·저널 정정 append)를 실행할 대상.
  WARN = 강등·구버전 흔적 — 보고에 명시. INFO = 참고.
  주의: doctor는 판정·저널 확정 후에 도는 사후 검증이라 그 자체로 승인을 차단하지 못한다(BLOCKING 아님).
  강제력은 오케스트레이터의 정정 루프 + 보고 명시 의무에서 나온다 — 각 스킬의 doctor 단계 참조.

종료 코드: FAIL ≥ 1이면 1, 아니면 0. 결과는 콘솔 요약 + JSON(기본 {workspace}/09_doctor.json).
사용:  python scripts/harness_doctor.py --harness trading|ipo|filings [--root DIR] [--json-out PATH]

한계(정직 명시): 텍스트 검사(④⑤⑥)는 휴리스틱이다 — 통과가 무결을 보증하지 않으며,
LLM 게이트(fact-checker·verdict-reviewer)를 대체하지 않고 보완한다.
"""
import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

# Windows 콘솔(cp949)에서 이모지 출력 크래시 방지
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FAIL, WARN, INFO, OK = "FAIL", "WARN", "INFO", "OK"

REQUIRED = {
    "trading": {
        "workspace": "_workspace",
        "fail_if_missing": [
            "00_input.md", "00_market_snapshot.json", "00_factcheck.md",
            "01_fundamental_report.md", "01_technical_report.md",
            "01_news_report.md", "01_sentiment_report.md",
            "02_bull_thesis.md", "02_bear_thesis.md",
            "02_bull_rebuttal.md", "02_bear_rebuttal.md",
            "03_research_plan.md", "04_trade_plan.md",
            "05_risk_aggressive.md", "05_risk_neutral.md", "05_risk_conservative.md",
            "05_portfolio_impact.md",  # 2026-07-03 이후 필수 — 구 실행분은 FAIL로 드러나는 게 정직하다
            "06_final_decision.md",
        ],
        "warn_if_missing": [
            "00_macro_regime.md",      # 배경 레이어 — 차단 아님(스킬 정의와 동일)
            "08_plain_explanation.md", # 표준 산출물
        ],
    },
    "ipo": {
        "workspace": "_workspace_ipo",
        "fail_if_missing": [
            "00_orchestrator_input.md", "00_ipo_snapshot.json",
            "01_bull_report.md", "01_bear_report.md",
            "02_factchecker_annotations.md", "03_judge_verdict.md",
            "03b_verdict_review.md", "03c_ipo_entry_plan.md", "03d_execution_review.md",
        ],
        "warn_if_missing": ["05_plain_explanation.md"],
    },
    "filings": {
        "workspace": "_workspace_filings",
        "fail_if_missing": [
            "00_input.md", "00_filings_facts.json", "00_audit.md",
            "01_financial_report.md", "01_mdna_report.md",
            "01_segment_report.md", "01_risk_report.md",
            "03_synthesis.md", "03b_synthesis_review.md",
        ],
        "warn_if_missing": ["04_plain_explanation.md"],
    },
}


class Doctor:
    def __init__(self, harness: str, root: Path):
        self.harness = harness
        self.root = root
        self.ws = root / REQUIRED[harness]["workspace"]
        self.checks = []

    def add(self, check_id: str, severity: str, message: str):
        self.checks.append({"id": check_id, "severity": severity, "message": message})

    def read(self, name: str):
        p = self.ws / name
        if not p.exists():
            return None
        try:
            # utf-8-sig: Windows 외부 편집(PowerShell·메모장)의 BOM 유무 모두 수용
            return p.read_text(encoding="utf-8-sig", errors="replace")
        except Exception as e:
            self.add(f"read:{name}", WARN, f"{name} 읽기 실패: {e}")
            return None

    # ── 1. 필수 산출물 ──────────────────────────────────────────────
    def check_artifacts(self):
        spec = REQUIRED[self.harness]
        if not self.ws.exists():
            self.add("workspace", FAIL, f"작업공간 없음: {self.ws}")
            return
        for name in spec["fail_if_missing"]:
            if not (self.ws / name).exists():
                self.add(f"artifact:{name}", FAIL, f"필수 산출물 누락: {name}")
            else:
                self.add(f"artifact:{name}", OK, f"존재: {name}")
        for name in spec["warn_if_missing"]:
            if not (self.ws / name).exists():
                self.add(f"artifact:{name}", WARN, f"표준 산출물 누락: {name}")

    # ── 2·3. 스냅샷 필드 + 산술 (trading) ──────────────────────────
    def check_trading_snapshot(self):
        raw = self.read("00_market_snapshot.json")
        if raw is None:
            return
        try:
            snap = json.loads(raw)
        except json.JSONDecodeError as e:
            self.add("snapshot:parse", FAIL, f"스냅샷 JSON 파싱 실패: {e}")
            return

        for field in ("as_of", "market_session"):
            if field == "market_session" and _dig(snap, "session", "market_session"):
                # v1.1: 세션 앵커가 session 블록으로 이전 — 최상위 필드를 요구하지 않는다(허위 WARN 방지)
                self.add("snapshot:market_session", OK,
                         f"session.market_session = {_dig(snap, 'session', 'market_session')}")
                continue
            if not snap.get(field):
                self.add(f"snapshot:{field}", WARN, f"스냅샷에 {field} 없음 — 시점·세션 앵커 약화")
            else:
                self.add(f"snapshot:{field}", OK, f"{field} = {snap[field]}")

        # v1.1+ 스키마: session 블록(수집 레이어 기계 판정) 필수. 발동 조건은 schema_version 라벨(LLM 작성)만이
        # 아니라 기계 산출(00_indicators.json의 session 존재)도 본다 — 라벨을 1.0으로 적어 옵트아웃하는 구멍 차단
        ver_raw = str(snap.get("schema_version", "1.0"))
        try:
            ver = tuple(int(x) for x in ver_raw.split("."))
        except ValueError:
            self.add("snapshot:schema", WARN,
                     f"schema_version 파싱 불가('{ver_raw}') — v1.1로 간주하고 검사(fail-safe)")
            ver = (1, 1)
        ind = {}
        ind_raw = self.read("00_indicators.json")
        if ind_raw:
            try:
                ind = json.loads(ind_raw)
            except json.JSONDecodeError:
                ind = {}
        ind_sess = ind.get("session") or {}
        sess = snap.get("session") or {}

        # 기계 산출(00_indicators.json) 부재의 가시화 — 파일 하나 없다고 기계 검증 레이어가 조용히 꺼지지 않게
        if not ind:
            if sess and str(sess.get("calendar_status", "")) == "manual":
                self.add("snapshot:session.machine", WARN,
                         "session 블록 수동 작성(calendar_status:manual) — 수집 스크립트 실패 경로. 복사 충실성·교차 검증 미수행")
            elif sess:
                self.add("snapshot:session.machine", FAIL,
                         "스냅샷에 session 블록이 있는데 00_indicators.json 부재/파싱 불가 — 기계 산출 없이 session 자기선언"
                         " (수동 작성이면 calendar_status:'manual' 표기 필요)")
            else:
                self.add("snapshot:machine", WARN,
                         "00_indicators.json 부재/파싱 불가 — 기계 검증 레이어(session 복사 충실성·cross_check) 비활성")

        if ver >= (1, 1) or ind_sess:
            missing = [k for k in ("market_session", "data_as_of", "requested_at_utc") if not sess.get(k)]
            if missing:
                basis = f"schema {ver_raw}" if ver >= (1, 1) else "00_indicators.json에 기계 session 블록 존재"
                self.add("snapshot:session", FAIL,
                         f"{basis}인데 스냅샷 session 블록 불완전 — 누락: {', '.join(missing)}")
            else:
                self.add("snapshot:session", OK,
                         f"session 블록 OK ({sess['market_session']}, data_as_of={sess['data_as_of']})")
            # 신선도 경고는 기계값(ind_sess) 우선으로 발동 — LLM이 필드를 생략해도 무력화되지 않게
            fresh = ind_sess if ind_sess else sess
            if fresh.get("anomaly"):
                self.add("snapshot:session.anomaly", FAIL,
                         f"수집 스크립트가 이상 상태를 보고: {fresh['anomaly']} — 데이터·판정 시각 정합 확인 전 사용 금지")
            if fresh.get("last_close_is_final") is False:
                self.add("snapshot:session.final", WARN,
                         "last_close_is_final=false — 마지막 행이 미확정 세션 값. price가 직전 확정 종가인지 확인")
            if fresh.get("stale_feed_suspect") is True:
                self.add("snapshot:session.stale", WARN,
                         "stale_feed_suspect=true — 예상 최종 거래일보다 데이터가 뒤처짐(휴장일 가능성 포함, 원인 확인)")
            if fresh.get("intraday_data_gap") is True:
                self.add("snapshot:session.gap", WARN,
                         "intraday_data_gap=true — 장중 세션인데 당일 봉 없음(평일 휴장 또는 피드 미갱신). 세션 서술 확인")
            # '기계값 그대로 복사 [HARD]' 충실성 — 데이터 사실 필드 불일치는 FAIL, 판정 시각 의존 필드는 WARN
            if ind_sess and sess:
                for k, sev in (("data_as_of", FAIL), ("last_close_is_final", FAIL),
                               ("stale_feed_suspect", FAIL), ("intraday_data_gap", FAIL),
                               ("market_session", WARN), ("requested_at_utc", WARN)):
                    if k in ind_sess and k in sess and sess[k] != ind_sess[k]:
                        self.add(f"snapshot:session.copy.{k}", sev,
                                 f"session.{k}가 기계값과 불일치 — 스냅샷 {sess[k]!r} vs 00_indicators.json {ind_sess[k]!r}"
                                 " (그대로 복사 규칙 위반 또는 부분 재실행 후 미복사)")
                # 기계값이 존재하는 신선도 필드를 스냅샷에서 생략하는 우회 차단 (생략=복사 위반)
                for k in ("last_close_is_final", "stale_feed_suspect", "intraday_data_gap", "anomaly"):
                    if ind_sess.get(k) is not None and k not in sess:
                        self.add(f"snapshot:session.copy.{k}", FAIL,
                                 f"기계 session.{k}가 존재하는데 스냅샷에서 생략 — 전체 복사 규칙 위반")

        price = _num(_dig(snap, "price", "value"))
        if price is None:
            self.add("snapshot:price", FAIL, "price.value 없음 또는 비수치")
        if not _dig(snap, "price", "source"):
            self.add("snapshot:price.source", WARN, "price.source 없음 — 출처 추적 불가")

        # 산술: 시총 = 가격 × 주식수 (오차 5% 초과 FAIL, 1~5% WARN)
        # ETF·펀드류는 NAV 프리미엄/디스카운트로 정당한 괴리 가능 → FAIL 대신 WARN
        mcap = _num(_dig(snap, "market_cap", "value"))
        shares = _num(_dig(snap, "shares_outstanding", "value"))
        is_fund = bool(re.search(r"etf|fund", str(snap.get("asset_class", "")), re.I))
        if price is not None and mcap is not None and shares is not None and mcap > 0:
            calc = price * shares
            err = abs(calc - mcap) / mcap
            if err > 0.05:
                self.add("snapshot:mcap", WARN if is_fund else FAIL,
                         f"시총 산술 불일치: 가격×주식수={calc:,.0f} vs market_cap={mcap:,.0f} (오차 {err:.1%})"
                         + (" — 펀드류(NAV 괴리 가능)라 WARN" if is_fund else ""))
            elif err > 0.01:
                self.add("snapshot:mcap", WARN, f"시총 산술 근사 불일치 (오차 {err:.1%})")
            else:
                self.add("snapshot:mcap", OK, f"시총 검산 통과 (오차 {err:.2%})")

        # 산술: 신규가 ≈ 직전 × (1 + 등락률) — prev_close는 객체({value:...}) 또는 스칼라 둘 다 수용
        prev = _num_or_value(_dig(snap, "price_history", "prev_close"))
        chg = _num_or_value(_dig(snap, "price_history", "daily_change_pct"))
        if price is not None and prev is not None and chg is not None and price > 0:
            calc = prev * (1 + chg / 100.0)
            err = abs(calc - price) / price
            if err > 0.01:
                self.add("snapshot:chg", WARN,
                         f"등락률 vs 레벨 불일치: prev×(1+chg)={calc:,.2f} vs price={price:,.2f} (오차 {err:.1%})")
            else:
                self.add("snapshot:chg", OK, "등락률 검산 통과")
        else:
            self.add("snapshot:chg", INFO, "등락률 검산 미수행(prev_close/daily_change_pct 미확보) — 조용한 스킵 방지 표기")

        # 신선도 (참고용 — doctor를 나중에 돌리면 자연히 벌어진다. 3일: 주말+휴일 허용폭)
        as_of = _parse_date(str(snap.get("as_of", "")))
        if as_of:
            age = (date.today() - as_of).days
            if age > 3:
                self.add("snapshot:freshness", INFO, f"스냅샷 as_of가 {age}일 전 — 재실행 시 갱신 필요")

        # 이중 소스 교차(수집 스크립트 cross_check) ↔ 결정문 DEGRADED_DATA 정합
        if ind:
            xc = ind.get("cross_check") or {}
            status = str(xc.get("status", ""))
            if status == "mismatch":
                decision = self.read("06_final_decision.md") or ""
                if "DEGRADED_DATA" not in decision:
                    # risk-gate ①이 mismatch→DEGRADED_DATA를 하드룰로 선언하므로 여기도 FAIL(라벨 모순 — 정정 루프 대상)
                    self.add("snapshot:xcheck", FAIL,
                             f"이중 소스 종가 불일치(diff {xc.get('diff_pct')}% > 허용 {xc.get('tolerance_pct')}%)"
                             " — 결정문에 DEGRADED_DATA 표기 없음 (risk-gate ① 위반)")
                else:
                    self.add("snapshot:xcheck", OK, "이중 소스 불일치가 DEGRADED_DATA로 표기됨")
            elif status == "match":
                self.add("snapshot:xcheck", OK,
                         f"이중 소스 종가 일치 ({xc.get('secondary')}, diff {xc.get('diff_pct')}%)")
            elif status == "skipped_primary_is_fallback":
                self.add("snapshot:xcheck", WARN,
                         "1차 소스가 폴백(stooq) — 이중 소스 교차 없음(가장 미검증 경로). "
                         "스냅샷 price.confidence ≤ medium + 웹 교차 여부 확인")
            elif status.startswith("skipped_error"):
                self.add("snapshot:xcheck", INFO, f"이중 소스 교차 미수행: {status[:100]}")
            elif status.startswith("skipped"):
                self.add("snapshot:xcheck", INFO, f"이중 소스 교차 스킵: {status} (의도된 경로 — 감사 표기)")

    # ── 4·5. 최종 결정 ↔ 게이트·모드 정합 (trading) ────────────────
    def check_trading_decision(self):
        decision = self.read("06_final_decision.md")
        if decision is None:
            return

        # 판정 토큰 추출 (첫 '판정:' 줄)
        m = re.search(r"판정\s*[:：]\s*\**\s*(CONDITIONAL_APPROVE|APPROVE|REVISE|REJECT)", decision)
        verdict = m.group(1) if m else None
        if verdict is None:
            self.add("decision:verdict", WARN, "06_final_decision.md에서 판정 토큰을 찾지 못함")

        # 리스크 토론 ⛔치명 존재 여부.
        # 범례/템플릿 라인('⛔치명 | ⚠️중대 | ℹ️경미' 나열)은 심각도 기호 2종 이상 공존으로 식별해 제외
        # — 채워진 표 행('| 심각도 | ⛔치명 |')은 기호 1종뿐이라 정상 탐지된다.
        # 기호는 베이스 코드포인트(U+26A0/U+2139)로 매칭 — 변형 선택자(VS16) 유무 모두 수용.
        fatal_found = []
        for name in ("05_risk_aggressive.md", "05_risk_neutral.md", "05_risk_conservative.md"):
            text = self.read(name)
            if not text:
                continue
            for line in text.splitlines():
                if re.search(r"심각도\s*[:：].*⛔", line) and not re.search(r"[⚠ℹ]", line):
                    fatal_found.append(name)
                    break
        # ⛔치명은 CONDITIONAL_APPROVE로도 흡수 불가(risk-gate: 조건부 승인은 ⚠️경고 흡수 전용)
        if fatal_found and verdict in ("APPROVE", "CONDITIONAL_APPROVE"):
            # 해소 마커는 risk-gate가 규정한 밀착 포맷("REVISE 해소:")만 인정 — 부정문 오매칭 방지
            resolved = re.search(r"REVISE\s*해소\s*[:：]", decision)
            sev = WARN if resolved else FAIL
            self.add("decision:fatal-vs-approve", sev,
                     f"리스크 토론 ⛔치명 존재({', '.join(fatal_found)}) + 승인 판정({verdict}) — "
                     + ("결정문에 'REVISE 해소:' 마커 존재 → WARN(해소 여부 원문 확인 필요)" if resolved
                        else "⛔치명이면 승인 불가(risk-gate 판정 규칙 위반)"))

        # 조건부 승인 미스라벨: 조건을 붙였으면 CONDITIONAL_APPROVE여야 한다 (라벨-실체 일치의 기계 검사).
        # 문서 전체가 아니라 '판정'이 있는 줄만 본다 — 규칙 인용·부정문("조건부 승인이 아니다") 오탐 방지.
        if verdict == "APPROVE":
            for line in decision.splitlines():
                if (re.search(r"판정", line)
                        and re.search(r"조건부 승인|조건 \d+\s*건", line)
                        and not re.search(r"아니|아닙|않", line)):
                    self.add("decision:conditional-mislabel", FAIL,
                             f"판정 줄이 APPROVE인데 같은 줄에서 조건부 승인/조건 N건 언급 — CONDITIONAL_APPROVE로 표기해야 함: {line.strip()[:80]}")
                    break

        # 검증 모드 라벨 존재 (2026-07-04 이후 표준)
        if not re.search(r"FULLY_VERIFIED|DEGRADED_DATA|검증 모드", decision):
            self.add("decision:verification-mode", WARN,
                     "결정문에 검증 모드(FULLY_VERIFIED/DEGRADED_DATA) 표기 없음 — 구 템플릿 실행분")

        # 팩트체크 강등 → DEGRADED_DATA 표기 정합
        # 강등 서술은 여러 줄에 걸칠 수 있어 두 토큰을 파일 전역에서 독립 검색한다(WARN 등급 휴리스틱).
        factcheck = self.read("00_factcheck.md")
        if factcheck and "미확인" in factcheck and "강등" in factcheck:
            if "DEGRADED_DATA" not in decision:
                self.add("decision:degraded-label", WARN,
                         "팩트체크에 '미확인' 강등 흔적이 있는데 결정문에 DEGRADED_DATA 표기 없음")

        # 포트폴리오 모드 정합
        pj = self.root / "decisions" / "portfolio.json"
        holdings, pf_as_of = None, None
        if pj.exists():
            try:
                pdata = json.loads(pj.read_text(encoding="utf-8-sig"))
                holdings = pdata.get("holdings")
                pf_as_of = _parse_date(str(pdata.get("as_of") or ""))
            except Exception as e:
                self.add("portfolio:parse", WARN, f"portfolio.json 파싱 실패: {e}")
        impact = self.read("05_portfolio_impact.md") or ""
        combined = decision + "\n" + impact
        if holdings is not None and len(holdings) == 0:
            if "PORTFOLIO_AWARE" in combined:
                self.add("portfolio:mode", FAIL,
                         "holdings가 비어 있는데 PORTFOLIO_AWARE 라벨 사용 — SINGLE_TRADE_ONLY여야 함")
            elif "SINGLE_TRADE_ONLY" not in combined:
                self.add("portfolio:mode", WARN,
                         "holdings 비어 있음 — 결정문/영향 보고서에 SINGLE_TRADE_ONLY 라벨 없음(구 실행분)")
            else:
                self.add("portfolio:mode", OK, "SINGLE_TRADE_ONLY 라벨 정합")
        elif holdings:
            # 90일: portfolio-risk 스킬의 PORTFOLIO_STALE 기준과 동일. as_of 미기재도 STALE(기준 시점 불명)
            if (pf_as_of is None or (date.today() - pf_as_of).days > 90) and "PORTFOLIO_STALE" not in combined:
                self.add("portfolio:mode", WARN,
                         f"portfolio.json as_of={pf_as_of or '미기재'} — 90일 초과/불명이면 PORTFOLIO_STALE 라벨 필요")

        # 티커 정합: 워크스페이스 회전을 건너뛰고 직전 종목 파일이 섞이는 사고 방지 (run-id의 저비용 대체).
        # 각 파일에서 티커꼴 토큰(영숫자 2~12자, 접미 거래소 제거) 집합을 뽑아 쌍별 교집합으로 비교
        # — "(MKIF, 맥쿼리인프라)"·"(088980 / MKIF)"·"(티커 088980 / 088980.KS)" 같은 병기 포맷을 모두 수용.
        def _ticker_tokens(text: str) -> set:
            return {t.split(".")[0].upper() for t in re.findall(r"[A-Za-z0-9.]{2,12}", text)}

        sets = {}
        in_line = next((l for l in (self.read("00_input.md") or "").splitlines()
                        if re.search(r"대상\s*[:：]", l)), "")
        if _ticker_tokens(in_line):
            sets["00_input.md"] = _ticker_tokens(in_line)
        try:
            snap_ticker = json.loads(self.read("00_market_snapshot.json") or "{}").get("ticker")
            if snap_ticker:
                sets["00_market_snapshot.json"] = {str(snap_ticker).split(".")[0].upper()}
        except json.JSONDecodeError:
            pass
        m_dec = re.search(r"^# 최종 결정.*\(([^)]{1,40})\)", decision, re.M)
        if m_dec and _ticker_tokens(m_dec.group(1)):
            sets["06_final_decision.md"] = _ticker_tokens(m_dec.group(1))
        names = sorted(sets)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if not (sets[names[i]] & sets[names[j]]):
                    self.add("run:ticker-mismatch", WARN,
                             f"{names[i]} ↔ {names[j]} 티커 공통 토큰 없음(서로 다른 실행분 혼입 의심)")
                    break

    # ── IPO 전용 ────────────────────────────────────────────────────
    def check_ipo_snapshot(self):
        raw = self.read("00_ipo_snapshot.json")
        if raw is None:
            return
        try:
            snap = json.loads(raw)
        except json.JSONDecodeError as e:
            self.add("snapshot:parse", FAIL, f"IPO 스냅샷 JSON 파싱 실패: {e}")
            return
        overall = _dig(snap, "self_check", "overall")
        if overall is None:
            self.add("snapshot:self_check", FAIL, "self_check.overall 없음 — Phase 1.6 하드 게이트 미수행 의심")
        elif str(overall).upper() != "PASS":
            self.add("snapshot:self_check", FAIL, f"self_check.overall = {overall} (PASS 아님)")
        else:
            self.add("snapshot:self_check", OK, "self_check PASS")

    # ── 공시 경계 (filings) ─────────────────────────────────────────
    def check_filings_boundary(self):
        patterns = [
            (r"(매수|매도|청약)\s*(추천|권고|의견)", "매매 추천 언어"),
            (r"\b(BUY|SELL)\b\s*(판정|추천)?", "BUY/SELL 판정 언어"),
        ]
        for name in ("03_synthesis.md", "04_plain_explanation.md"):
            text = self.read(name)
            if not text:
                continue
            hits = []
            # 줄 단위 매칭 — finditer의 오프셋→줄번호 환산과 splitlines 불일치(단독 \r 등) 방지
            for lineno, ctx in enumerate(text.splitlines(), start=1):
                # 부정 문맥("판단이 아니다/아닙니다", "하지 않는다", 면책, 트레이딩 하네스 안내)은 제외
                if re.search(r"아니|아닙|않|없|금지|면책|trading-strategy|트레이딩 하네스", ctx):
                    continue
                for pat, label in patterns:
                    if re.search(pat, ctx):
                        hits.append(f"{name}:{lineno} ({label})")
                        break
            if hits:
                self.add(f"boundary:{name}", WARN,
                         "매매 판단 언어 의심(휴리스틱 — 원문 확인 필요): " + "; ".join(hits[:5]))
            else:
                self.add(f"boundary:{name}", OK, f"{name} 매매 언어 미검출")

    # ── 실행 ────────────────────────────────────────────────────────
    def run(self):
        self.check_artifacts()
        if self.harness == "trading":
            self.check_trading_snapshot()
            self.check_trading_decision()
        elif self.harness == "ipo":
            self.check_ipo_snapshot()
        elif self.harness == "filings":
            self.check_filings_boundary()
        return self.result()

    def result(self):
        counts = {s: sum(1 for c in self.checks if c["severity"] == s) for s in (FAIL, WARN, INFO, OK)}
        verdict = "FAIL" if counts[FAIL] else ("WARN" if counts[WARN] else "GREEN")
        return {
            "harness": self.harness,
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "workspace": str(self.ws),
            "verdict": verdict,
            "summary": counts,
            "checks": self.checks,
        }


def _dig(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _num(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.replace(",", ""))
        except ValueError:
            return None
    return None


def _num_or_value(v):
    """스칼라 또는 {value: ...} 객체 둘 다에서 수치를 꺼낸다 — 스냅샷 필드가 스키마 세대에 따라 혼재."""
    if isinstance(v, dict):
        v = v.get("value")
    return _num(v)


def _parse_date(s: str):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description="trading-agent harness doctor")
    ap.add_argument("--harness", choices=list(REQUIRED), default="trading")
    ap.add_argument("--root", default=".", help="저장소 루트 (기본: 현재 디렉토리)")
    ap.add_argument("--json-out", default=None, help="JSON 결과 경로 (기본: {workspace}/09_doctor.json)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    doctor = Doctor(args.harness, root)
    result = doctor.run()

    out = Path(args.json_out) if args.json_out else doctor.ws / "09_doctor.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[WARN] JSON 저장 실패({out}): {e}")

    print(f"harness doctor — {args.harness} @ {doctor.ws}")
    print(f"verdict: {result['verdict']}  "
          f"(FAIL {result['summary'][FAIL]} / WARN {result['summary'][WARN]} / "
          f"INFO {result['summary'][INFO]} / OK {result['summary'][OK]})")
    for c in result["checks"]:
        if c["severity"] in (FAIL, WARN, INFO):
            print(f"  [{c['severity']}] {c['id']} — {c['message']}")
    print(f"json: {out}")
    sys.exit(1 if result["summary"][FAIL] else 0)


if __name__ == "__main__":
    main()
