#!/usr/bin/env python3
"""NotebookLM 오디오(팟캐스트) 생성 — notebooklm-py CLI 래퍼.

대본/보고서 마크다운을 NotebookLM 노트북에 소스로 추가하고, Audio Overview
(팟캐스트)를 생성·다운로드한다. NotebookLM은 소스를 받아 오디오를 *자체 재생성*
하므로(대본 그대로 낭독 아님), 대본+보고서를 소스로 넣고 format/지침으로 유도한다.

사전 요구 (사용자가 1회 직접 수행):
  pip install "notebooklm-py[browser]"
  playwright install chromium
  notebooklm login        # 대화형 Google 로그인 — 스크립트로 대신 불가

사용 예:
  python generate_audio.py --out podcast.mp3 \
      --source 03_judge_verdict.md --source 04_producer_podcast.md \
      --title "삼성전자 투자 분석" --format debate --length default --language ko \
      --instructions "강세 vs 약세를 토론하되 최종 결론은 HOLD(중립 보유)임을 분명히 전달"

종료 코드: 0 성공 / 2 인증 미완료(로그인 필요) / 3 CLI 미설치 / 1 기타 오류
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def eprint(*a: object) -> None:
    print(*a, file=sys.stderr)


def find_cli_candidates() -> list[str]:
    """PATH의 모든 notebooklm 실행 후보를 순서대로 모은다.
    깨진 셰임이 정상 설치본을 가리는 경우(예: ~/bin의 손상된 exe)를 대비해
    하나가 아니라 후보 전체를 반환하고, 호출부에서 실행 가능한 것을 고른다."""
    candidates: list[str] = []
    seen: set[str] = set()

    def add(path: str | os.PathLike[str]) -> None:
        s = str(path)
        key = os.path.normcase(s)
        if key not in seen and Path(s).exists():
            candidates.append(s)
            seen.add(key)

    # 1순위: shutil.which (PATHEXT 고려). git-bash에서는 ~/bin의 셰임이 먼저 잡힐 수 있다.
    primary = shutil.which("notebooklm")
    if primary:
        add(primary)

    exts = os.environ.get("PATHEXT", ".EXE;.CMD;.BAT").split(os.pathsep) if os.name == "nt" else [""]

    # 2순위: PATH 전수
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d:
            continue
        for ext in [""] + exts:
            add(Path(d) / f"notebooklm{ext}")

    # 3순위: pip 설치 위치(현재 인터프리터 + 사용자 site)의 Scripts 디렉토리.
    # PATH에 없더라도 정상 설치된 console script(notebooklm.exe)를 직접 찾기 위함.
    script_dirs: list[str] = []
    for scheme_args in ((), ("nt_user",), ("posix_user",)):
        try:
            script_dirs.append(sysconfig.get_path("scripts", *scheme_args))
        except (KeyError, OSError):
            continue
    for d in script_dirs:
        if not d:
            continue
        for ext in [""] + exts:
            add(Path(d) / f"notebooklm{ext}")

    return candidates


def resolve_runnable_cli() -> tuple[str | None, bool]:
    """실행 가능한 notebooklm CLI를 찾는다.
    반환: (cli경로, 인증성공여부). 후보를 차례로 auth check 해 보고,
    실행 자체가 되는(=설치/호환 OK) 첫 후보를 채택한다."""
    candidates = find_cli_candidates()
    if not candidates:
        return None, False
    last_unrunnable: str | None = None
    for cli in candidates:
        try:
            auth = run(cli, ["auth", "check", "--test", "--json"], timeout=120)
        except CliUnrunnable as e:
            eprint(f"[skip] 실행 불가 후보: {cli} ({e})")
            last_unrunnable = cli
            continue
        return cli, _auth_ok(auth)
    # 모든 후보가 실행 불가
    if last_unrunnable:
        raise CliUnrunnable(f"PATH의 모든 notebooklm 후보가 실행 불가 (마지막: {last_unrunnable})")
    return None, False


def _auth_ok(auth: subprocess.CompletedProcess[str]) -> bool:
    if auth.returncode != 0:
        return False
    data = parse_json(auth.stdout)
    if isinstance(data, dict):
        for key in ("ok", "valid", "authenticated", "logged_in", "success"):
            if key in data and data[key] is False:
                return False
    return True


class CliUnrunnable(RuntimeError):
    """CLI 파일은 있으나 실행 자체가 불가한 경우(미설치 동급)."""


def run(cli: str, args: list[str], *, capture: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    """notebooklm CLI를 호출한다. shell=False로 인자 주입 위험을 차단한다.
    실행 파일이 깨졌거나(WinError 216 등) 없으면 CliUnrunnable로 변환한다."""
    cmd = [cli, *args]
    eprint(f"[run] {' '.join(cmd)}")
    try:
        return subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as e:
        # WinError 216(호환 안 됨), 2(파일 없음) 등 — 실행 불가
        raise CliUnrunnable(str(e)) from e


def parse_json(stdout: str) -> object | None:
    stdout = (stdout or "").strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        # 마지막 JSON 라인만 파싱 시도 (로그가 앞에 섞인 경우)
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if line.startswith("{") or line.startswith("["):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    return None


def find_notebook_id(obj: object, stdout: str) -> str | None:
    """JSON에서 노트북 id를 방어적으로 추출한다. 키 이름이 불확실하므로
    'id'/'notebook'를 포함한 키를 우선 보고, 실패하면 UUID 패턴을 찾는다."""
    def walk(o: object) -> str | None:
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and ("notebook" in k.lower() and "id" in k.lower()):
                    return v
            for k, v in o.items():
                if isinstance(v, str) and k.lower() in ("id", "notebook_id", "notebookid"):
                    return v
            for v in o.values():
                r = walk(v)
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = walk(v)
                if r:
                    return r
        return None

    rid = walk(obj) if obj is not None else None
    if rid:
        return rid
    m = UUID_RE.search(stdout or "")
    return m.group(0) if m else None


def find_audio_artifact_id(obj: object) -> str | None:
    """`artifact list --json` 출력에서 오디오 artifact id를 고른다.
    여러 개면 created_at 기준 최신을 택한다(노트북은 매 실행 새로 만들므로 보통 1개)."""
    if not isinstance(obj, dict):
        return None
    arts = obj.get("artifacts")
    if not isinstance(arts, list):
        return None
    audio = [a for a in arts if isinstance(a, dict)
             and (a.get("type_id") == "audio" or a.get("type") == "Audio")]
    if not audio:
        audio = [a for a in arts if isinstance(a, dict) and a.get("id")]
    if not audio:
        return None
    audio.sort(key=lambda a: str(a.get("created_at") or a.get("index") or ""))
    return audio[-1].get("id")


def main() -> int:
    ap = argparse.ArgumentParser(description="NotebookLM 팟캐스트 생성")
    ap.add_argument("--out", required=True, help="다운로드할 MP3 출력 경로")
    ap.add_argument("--source", action="append", default=[], required=True,
                    help="소스 마크다운/파일 경로 (반복 지정 가능)")
    ap.add_argument("--title", default="Investment Analysis", help="노트북 제목")
    ap.add_argument("--format", default="debate",
                    choices=["deep-dive", "brief", "critique", "debate"],
                    help="오디오 포맷 (강세 vs 약세에는 debate 권장)")
    ap.add_argument("--length", default="default", choices=["short", "default", "long"])
    ap.add_argument("--language", default="ko", help="언어 코드 (기본 ko)")
    ap.add_argument("--instructions", default="", help="생성 유도 지침 (한국어)")
    ap.add_argument("--gen-timeout", type=int, default=2700, help="오디오 생성 대기 타임아웃(초). NotebookLM debate 생성은 30분 초과 사례 관찰됨")
    ap.add_argument("--interval", type=int, default=5, help="생성 상태 폴링 간격(초)")
    ap.add_argument("--source-timeout", type=int, default=300, help="소스 인입 타임아웃(초)")
    ap.add_argument("--check-only", action="store_true", help="설치/인증 사전점검만 수행")
    args = ap.parse_args()

    # 1) 실행 가능한 CLI 탐색 + 인증 확인 (비대화형). 깨진 셰임은 건너뛴다.
    try:
        cli, authed = resolve_runnable_cli()
    except CliUnrunnable as e:
        eprint(f"[ERROR] notebooklm 실행 불가: {e}")
        eprint("손상된 실행 파일이 PATH를 가리고 있을 수 있습니다. 올바르게 재설치하세요:")
        eprint('  pip install "notebooklm-py[browser]" && playwright install chromium')
        return 3
    if not cli:
        eprint("[ERROR] 'notebooklm' CLI를 찾을 수 없습니다.")
        eprint('설치: pip install "notebooklm-py[browser]" && playwright install chromium')
        return 3
    eprint(f"[info] notebooklm CLI = {cli}")
    if not authed:
        eprint("[ERROR] NotebookLM 인증이 필요합니다 (auth check 실패).")
        eprint("터미널에서 직접 로그인하세요: notebooklm login")
        eprint("(Claude Code 세션이면 프롬프트에 '! notebooklm login' 입력)")
        return 2

    if args.check_only:
        print(json.dumps({"status": "ready"}, ensure_ascii=False))
        return 0

    # 소스 경로 검증
    src_paths: list[Path] = []
    for s in args.source:
        p = Path(s).expanduser().resolve()
        if not p.exists():
            eprint(f"[ERROR] 소스 파일 없음: {p}")
            return 1
        src_paths.append(p)

    # 2) 노트북 생성 (id 추출). create --json → {"notebook":{"id":...}}
    created = run(cli, ["create", args.title, "--json"], timeout=180)
    if created.returncode != 0:
        eprint("[ERROR] 노트북 생성 실패:\n" + (created.stderr or created.stdout))
        return 1
    nb_id = find_notebook_id(parse_json(created.stdout), created.stdout)
    if not nb_id:
        eprint("[ERROR] 생성된 노트북 id를 파싱하지 못했습니다:\n" + created.stdout)
        return 1
    nb_args = ["-n", nb_id]
    eprint(f"[info] notebook id = {nb_id}")

    # 3) 소스 추가 (로컬 .md 경로 → 자동 감지로 text 소스). --type 미지정(auto).
    for p in src_paths:
        added = run(
            cli,
            ["source", "add", str(p), "--title", p.stem, *nb_args, "--json"],
            timeout=args.source_timeout + 60,
        )
        if added.returncode != 0:
            eprint(f"[ERROR] 소스 추가 실패 ({p.name}):\n" + (added.stderr or added.stdout))
            return 1

    # 4) 오디오 생성 제출 (--no-wait). `generate audio --wait`는 대기 한도가 300초로
    #    고정돼 긴 생성에서 끊기므로, 제출만 하고 artifact wait로 길게 기다린다.
    gen_args = ["generate", "audio"]
    if args.instructions:
        gen_args.append(args.instructions)
    gen_args += ["--format", args.format, "--length", args.length,
                 "--language", args.language, "--no-wait", "--retry", "2",
                 *nb_args, "--json"]
    gen = run(cli, gen_args, timeout=300)
    if gen.returncode != 0:
        eprint("[ERROR] 오디오 생성 제출 실패:\n" + (gen.stderr or gen.stdout))
        return 1

    # 4.5) 오디오 artifact id 확보 (artifact list로 조회 — 출력 형태가 확실).
    lst = run(cli, ["artifact", "list", *nb_args, "--json"], timeout=120)
    art_id = find_audio_artifact_id(parse_json(lst.stdout))
    if not art_id:
        eprint("[ERROR] 생성된 오디오 artifact를 찾지 못했습니다:\n" + (lst.stdout or lst.stderr))
        return 1
    eprint(f"[info] audio artifact id = {art_id}")

    # 4.6) 완료 대기 (긴 timeout으로 폴링).
    waited = run(
        cli,
        ["artifact", "wait", art_id, *nb_args,
         "--timeout", str(args.gen_timeout), "--interval", str(args.interval), "--json"],
        timeout=args.gen_timeout + 120,
    )
    if waited.returncode != 0:
        eprint("[ERROR] 오디오 생성 대기 실패/타임아웃:\n" + (waited.stderr or waited.stdout))
        eprint(f"(생성은 서버에서 계속될 수 있습니다. 나중에 'artifact wait {art_id}' 또는 'download audio'로 재시도 가능)")
        return 1

    # 5) 다운로드
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    dl = run(
        cli,
        ["download", "audio", str(out), "--latest", "--force", *nb_args, "--json"],
        timeout=600,
    )
    if dl.returncode != 0:
        eprint("[ERROR] 다운로드 실패:\n" + (dl.stderr or dl.stdout))
        return 1

    if not out.exists():
        eprint(f"[ERROR] 다운로드 후 파일이 없습니다: {out}")
        return 1

    print(json.dumps({
        "status": "ok",
        "notebook_id": nb_id,
        "output": str(out),
        "bytes": out.stat().st_size,
        "format": args.format,
        "language": args.language,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CliUnrunnable as e:
        eprint(f"[ERROR] notebooklm CLI 실행 불가: {e}")
        eprint('재설치: pip install "notebooklm-py[browser]" && playwright install chromium')
        sys.exit(3)
    except subprocess.TimeoutExpired as e:
        eprint(f"[ERROR] 시간 초과: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
