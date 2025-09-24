# app_core/chatbot_engine.py
from __future__ import annotations
import re, json
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import plotly.express as px

# ============ 표시용 맵/유틸 ============
DISPLAY_NAME = {
    "TOTAL":"합계",
    "AGE":"연령","BRAND":"브랜드","MODEL":"모델",
    "FUEL":"연료","IMPORT":"국산/수입",
    "SEG_SZ":"차급","SEG_BT":"외형","EXTRACT_DE":"연월",
}

def _fmt_ym(ym: str) -> str:
    s = str(ym).strip()
    return f"{s[:4]}-{s[4:]}" if len(s)==6 and s.isdigit() else s

# ============ 컬럼 후보(자동 매핑) ============
CAND_DIM = {
    "AGE":    ["AGE","연령","연령대"],
    "BRAND":  ["ORG_CAR_MAKER_KOR","브랜드","MANUFACTURER"],
    "MODEL":  ["CAR_MOEL_DT","CAR_MODEL_KOR","모델"],
    "FUEL":   ["FUEL","USE_FUEL_NM","연료"],
    "IMPORT": ["CL_HMMD_IMP_SE_NM","국산수입","세그먼트"],
    "CNT":    ["CNT","count","대수"],
    # 있으면 활용 (없어도 동작)
    "SEG_BT": ["CAR_BT","외형"],
    "SEG_SZ": ["CAR_SZ","차급"],
    "EXTRACT_DE": ["EXTRACT_DE","연월","날짜"],
}
CAND_SEG = {
    "EXTRACT_DE": ["EXTRACT_DE","연월","날짜"],
    "SEG_SZ":     ["CAR_SZ","차급"],
    "SEG_BT":     ["CAR_BT","외형"],
    "FUEL":       ["USE_FUEL_NM","FUEL","연료"],
    "CNT":        ["CNT","대수"],
}

# 값 사전(외형/차급/연료)
BODY_TYPE_WORDS = {
    "suv":"SUV","세단":"세단","rv":"RV","해치백":"해치백",
    "픽업":"픽업트럭","픽업트럭":"픽업트럭","컨버터블":"컨버터블",
    "쿠페":"쿠페","왜건":"왜건","웨건":"왜건","밴":"밴","미니밴":"밴",
}
SIZE_WORDS = {
    "경형":"경형","소형":"소형","준중형":"준중형","중형":"중형",
    "준대형":"준대형","대형":"대형",
}
FUEL_WORDS = {
    "휘발유":"휘발유","가솔린":"휘발유",
    "경유":"경유","디젤":"경유",
    "전기":"전기","ev":"전기",
    "하이브리드":"하이브리드",
    "lpg":"엘피지","엘피지":"엘피지",
}

def _resolve_cols(df: pd.DataFrame | None, cand: Dict[str, List[str]]) -> Dict[str, Optional[str]]:
    if not isinstance(df, pd.DataFrame):
        return {k: None for k in cand}
    lower = {c.lower(): c for c in df.columns}
    out: Dict[str, Optional[str]] = {}
    for key, options in cand.items():
        hit = None
        for name in options:
            if name in df.columns: hit = name; break
            if name.lower() in lower: hit = lower[name.lower()]; break
        out[key] = hit
    return out

# ============ 컨텍스트 로드 ============

def load_context() -> Dict[str, Any]:
    """
    data_loader에서 모두 적재, 컬럼 매핑/값 카탈로그 생성, 연월 표준화.
    반환: {frames, colmaps, has_er_detail, catalog}
    """
    from app_core import data_loader as dl
    ov = dl.get_overview_data(base_dir="data")
    nr = dl.get_newreg_data(base_dir="data")
    er = dl.get_ersr_data(base_dir="data")

    frames: Dict[str, pd.DataFrame | None] = {
        "신규(세그)": ov["new_seg"],
        "이전(세그)": ov["used_seg"],
        "말소(세그)": ov["er_seg"],
        "누적 상세":  nr["dim"],
        "말소 상세":  er.get("monthly"),
    }
    colmaps = {
        k: _resolve_cols(frames[k], CAND_SEG if "세그" in k else CAND_DIM) for k in frames
    }

    # EXTRACT_DE → 'YYYYMM' 문자열 통일
    def _normalize_ym(df: pd.DataFrame, col: str):
        if df is None or col not in df.columns: return
        def to_ym(v):
            if pd.isna(v): return pd.NA
            s = str(v).strip().replace(".0","")
            m = re.search(r"(20\d{2})\D?(\d{1,2})", s)
            if m:
                y, mo = int(m.group(1)), int(m.group(2)); return f"{y:04d}{mo:02d}"
            try:
                iv = int(float(s)); y, mo = iv//100, iv%100; return f"{y:04d}{mo:02d}"
            except: return s
        df[col] = df[col].map(to_ym)

    for key in ("신규(세그)","이전(세그)","말소(세그)","누적 상세","말소 상세"):
        c = colmaps[key].get("EXTRACT_DE")
        if c and isinstance(frames[key], pd.DataFrame): _normalize_ym(frames[key], c)

    # 값 카탈로그(브랜드/모델/연료/외형/차급)
    catalog: Dict[str, set] = {
        "brands": set(),
        "models": set(),
        "fuels":  set(),
        "bodys":  set(),
        "sizes":  set(),
    }
    dim = frames["누적 상세"]; cmap = colmaps["누적 상세"]
    if isinstance(dim, pd.DataFrame):
        if cmap.get("BRAND"): catalog["brands"] = set(dim[cmap["BRAND"]].dropna().astype(str).unique())
        if cmap.get("MODEL"): catalog["models"] = set(dim[cmap["MODEL"]].dropna().astype(str).unique())
        if cmap.get("FUEL"):  catalog["fuels"]  = set(dim[cmap["FUEL"]].dropna().astype(str).unique())
        # 일부 dim에 외형/차급이 있을 수도 있음
        if cmap.get("SEG_BT"): catalog["bodys"] = set(dim[cmap["SEG_BT"]].dropna().astype(str).unique())
        if cmap.get("SEG_SZ"): catalog["sizes"] = set(dim[cmap["SEG_SZ"]].dropna().astype(str).unique())

    seg_any = frames["신규(세그)"]; cmap_seg = colmaps["신규(세그)"]
    if isinstance(seg_any, pd.DataFrame):
        if cmap_seg.get("FUEL"):   catalog["fuels"] |= set(seg_any[cmap_seg["FUEL"]].dropna().astype(str).unique())
        if cmap_seg.get("SEG_BT"): catalog["bodys"] |= set(seg_any[cmap_seg["SEG_BT"]].dropna().astype(str).unique())
        if cmap_seg.get("SEG_SZ"): catalog["sizes"] |= set(seg_any[cmap_seg["SEG_SZ"]].dropna().astype(str).unique())

    return {
        "frames": frames,
        "colmaps": colmaps,
        "has_er_detail": isinstance(frames["말소 상세"], pd.DataFrame),
        "catalog": catalog,
    }

# ============ 질의 해석 ============

def parse_year_month(q: str) -> Optional[str]:
    s = q.replace(" ", "")
    m = re.search(r"(20\d{2})[./\-]?(0?[1-9]|1[0-2])|20(\d{2})년(0?[1-9]|1[0-2])월", s)
    if m:
        y = m.group(1) or f"20{m.group(3)}"; mo = m.group(2) or m.group(4)
        return f"{int(y):04d}{int(mo):02d}"
    m2 = re.search(r"(20\d{2})(0[1-9]|1[0-2])", s)
    return f"{int(m2.group(1)):04d}{int(m2.group(2)):02d}" if m2 else None

def detect_source(question: str, has_er_detail: bool) -> str:
    q = question
    if "신규" in q: return "신규(세그)"
    if ("이전" in q) or ("중고" in q): return "이전(세그)"
    if "말소" in q: return "말소 상세" if has_er_detail else "말소(세그)"
    if any(w in q for w in ["차급","외형","월","월별"]): return "신규(세그)"
    return "누적 상세"

def _find_value_in_text(text: str, candidates: set) -> Optional[str]:
    """
    텍스트에 포함된 후보값을 부분일치로 탐색(길이 긴 것 우선).
    """
    tl = text.lower()
    for cand in sorted({str(x) for x in candidates}, key=lambda s: -len(s)):
        if cand and cand.lower() in tl:
            return cand
    return None

def parse_query(question: str, source: str, catalog: Dict[str, set]) -> Dict[str, Any]:
    q = question.strip().lower()

    # 그룹 결정
    hints_group = ["연령","연령대","나이","브랜드","제조사","모델","차종","연료","국산/수입","세그먼트","차급","외형","월","월별"]
    if ("대수" in q) and not any(h in question for h in hints_group):
        group = "TOTAL"
    elif any(k in question for k in ["총","전체","합계","대수만","전체대수"]):
        group = "TOTAL"
    else:
        if source in ("누적 상세","말소 상세"):
            gmap = {"연령":"AGE","연령대":"AGE","나이":"AGE","브랜드":"BRAND","제조사":"BRAND",
                    "모델":"MODEL","차종":"MODEL","연료":"FUEL","국산/수입":"IMPORT","세그먼트":"IMPORT"}
            default = "BRAND"
        else:
            gmap = {"차급":"SEG_SZ","외형":"SEG_BT","연료":"FUEL","월별":"EXTRACT_DE","월":"EXTRACT_DE"}
            default = "SEG_SZ"
        group = next((v for k,v in gmap.items() if k in question), default)

    # 필터
    filters: List[Tuple[str,str,str]] = []

    # 연료
    for k,v in FUEL_WORDS.items():
        if k in q: filters.append(("FUEL","==", v)); break

    # 국산/수입
    if "국산" in question: filters.append(("IMPORT","==","국산"))
    elif "수입" in question: filters.append(("IMPORT","==","수입"))

    # 외형·차급 값(세분화)
    for k,v in BODY_TYPE_WORDS.items():
        if k in q: filters.append(("SEG_BT","==", v)); break
    for k,v in SIZE_WORDS.items():
        if k in q: filters.append(("SEG_SZ","==", v)); break

    # 브랜드/모델(부분일치)
    brand_hit = _find_value_in_text(question, catalog.get("brands", set()))
    model_hit = _find_value_in_text(question, catalog.get("models", set()))
    if brand_hit: filters.append(("BRAND","~", brand_hit))
    if model_hit: filters.append(("MODEL","~", model_hit))

    # 연월
    ym = parse_year_month(question)
    if ym: filters.append(("EXTRACT_DE","==", ym))

    # 상위N/정렬
    m = re.search(r"(상위|top)\s*(\d+)", question, re.IGNORECASE)
    topn = int(m.group(2)) if m else (10 if ("상위" in question or "top" in question.lower()) else None)
    sort = "asc" if ("오름차순" in question or "asc" in question.lower()) else "desc"

    # 등록구분 힌트(메타 용)
    reg_hint = "신규" if "신규" in question else "이전" if ("이전" in question or "중고" in question) else "말소" if "말소" in question else None

    return {"group": group, "filters": filters, "topn": topn, "sort": sort, "reg_hint": reg_hint}

def route_source(question: str, source: str, plan: Dict[str,Any], colmaps: Dict[str,Dict[str,Optional[str]]], has_er_detail: bool) -> str:
    """
    필요한 컬럼을 만족하는 소스로 자동 재라우팅
    """
    need_cols = set()
    if plan["group"] != "TOTAL": need_cols.add(plan["group"])
    for key,_,_ in plan["filters"]:
        need_cols.add(key)

    def has_cols(src: str) -> bool:
        cmap = colmaps.get(src, {})
        for k in need_cols:
            if k == "TOTAL": continue
            if cmap.get(k) is None: return False
        return True

    if has_cols(source):
        return source

    want_seg = any(k in need_cols for k in ["SEG_SZ","SEG_BT","EXTRACT_DE"])
    want_dim = any(k in need_cols for k in ["AGE","BRAND","MODEL","IMPORT","FUEL"])
    if want_seg:
        if "말소" in question: return "말소(세그)"
        if "이전" in question or "중고" in question: return "이전(세그)"
        return "신규(세그)"
    if want_dim:
        if "말소" in question and has_er_detail: return "말소 상세"
        return "누적 상세"

    return source

# ============ 집계 + 메타 ============

def execute(df: pd.DataFrame, plan: Dict[str, Any], colmap: Dict[str, Optional[str]], mode_label: str) -> Tuple[pd.DataFrame, dict]:
    """
    op:
      '=='  : 완전일치
      '~'   : 부분일치(대소문자 무시)
    """
    if not isinstance(df, pd.DataFrame): raise ValueError(f"'{mode_label}' 데이터프레임이 유효하지 않습니다.")
    d = df.copy()
    rows_before = len(d)

    applied = []
    for key, op, val in plan["filters"]:
        real = colmap.get(key)
        if real and real in d.columns:
            if op == "==":
                d = d[d[real] == val]
            elif op == "~":
                d = d[d[real].astype(str).str.contains(str(val), case=False, na=False)]
            applied.append({"key": key, "op": op, "val": val,
                            "real_col": real, "display_val": _fmt_ym(val) if key=="EXTRACT_DE" else val})

    rows_after = len(d)

    mcol = colmap.get("CNT")
    if not mcol: raise ValueError(f"'{mode_label}'에서 CNT 컬럼을 찾을 수 없습니다.")
    sum_after = int(d[mcol].sum())

    if plan["group"] == "TOTAL":
        out = pd.DataFrame([{"구분":"합계","대수": sum_after}])
        meta = {"source":mode_label,"group":plan["group"],"filters":applied,"sort":plan["sort"],"topn":plan["topn"],
                "rows_before":rows_before,"rows_after":rows_after,"sum_after":sum_after}
        return out, meta

    gcol = colmap.get(plan["group"])
    if not gcol or gcol not in d.columns:
        raise ValueError(f"요청한 기준({plan['group']})은(는) '{mode_label}' 데이터에서 지원되지 않습니다.")

    out = d.groupby(gcol, dropna=False)[mcol].sum().reset_index()
    out = out.rename(columns={gcol:"구분", mcol:"대수"})
    out["대수"] = out["대수"].astype(int)

    ascending = plan["sort"]=="asc"
    out = out.sort_values("대수", ascending=ascending)
    if plan["topn"]: out = out.head(plan["topn"])

    meta = {"source":mode_label,"group":plan["group"],"filters":applied,"sort":plan["sort"],"topn":plan["topn"],
            "rows_before":rows_before,"rows_after":rows_after,
            "sum_after": int(out["대수"].sum()) if not out.empty else 0}
    return out, meta

# ============ 상세 정보(브랜드/모델) ============

def vehicle_specs_from_sources(frames: Dict[str, pd.DataFrame],
                               colmaps: Dict[str, Dict[str, Optional[str]]],
                               brand_like: Optional[str],
                               model_like: Optional[str],
                               include: tuple[str, ...] = ("누적 상세", "신규(세그)")) -> pd.DataFrame:
    """
    누적 상세 + (신규/이전/말소) 세그 소스들에서 스펙 항목을 '합집합'으로 취합해
    대수 없이 '항목/값' 2열 표로 반환.
    - 브랜드/모델은 DIM(누적 상세)에서만 부분일치 필터를 적용.
    - 연료/차급/외형은 DIM/세그 모두에서 고유값을 모아 합집합.
    - 국산/수입은 DIM에 있을 때만 표기.
    """
    # 합집합 컨테이너
    brands: set[str] = set()
    models: set[str] = set()
    fuels:  set[str] = set()
    sizes:  set[str] = set()
    bodys:  set[str] = set()
    imports:set[str] = set()

    # 1) DIM(누적 상세): 브랜드/모델 필터 적용
    if "누적 상세" in include and isinstance(frames.get("누적 상세"), pd.DataFrame):
        dim = frames["누적 상세"].copy()
        cmap = colmaps.get("누적 상세", {})
        bcol, mcol = cmap.get("BRAND"), cmap.get("MODEL")

        if brand_like and bcol in dim.columns:
            dim = dim[dim[bcol].astype(str).str.contains(str(brand_like), case=False, na=False)]
        if model_like and mcol in dim.columns:
            dim = dim[dim[mcol].astype(str).str.contains(str(model_like), case=False, na=False)]

        def add_uniques(df: pd.DataFrame, col_key: str, target: set[str]):
            col = cmap.get(col_key)
            if col and col in df.columns:
                target |= set(df[col].dropna().astype(str).unique())

        add_uniques(dim, "BRAND", brands)
        add_uniques(dim, "MODEL", models)
        add_uniques(dim, "FUEL",  fuels)
        add_uniques(dim, "SEG_SZ", sizes)
        add_uniques(dim, "SEG_BT", bodys)
        add_uniques(dim, "IMPORT", imports)

    # 2) 세그 소스들: 브랜드/모델 컬럼이 보통 없으므로 연료/차급/외형만 합집합
    for src in include:
        if src == "누적 상세":
            continue
        df = frames.get(src)
        cmap = colmaps.get(src, {})
        if not isinstance(df, pd.DataFrame):
            continue
        def add(df, key, bag):
            col = cmap.get(key)
            if col and col in df.columns:
                bag |= set(df[col].dropna().astype(str).unique())
        add(df, "FUEL",  fuels)
        add(df, "SEG_SZ", sizes)
        add(df, "SEG_BT", bodys)

    # 3) 항목/값 표 구성
    def fmt(values: set[str]) -> str:
        vals = sorted({v for v in (values or set()) if v and v != "nan"})
        return ", ".join(vals) if vals else "-"

    rows = [
        ("브랜드",      fmt(brands)),
        ("모델",        fmt(models)),
        ("연료",        fmt(fuels)),
        ("차급",        fmt(sizes)),
        ("외형",        fmt(bodys)),
        ("국산/수입",   fmt(imports)),   # DIM에 없으면 '-'로 남음
    ]
    return pd.DataFrame(rows, columns=["항목", "값"])

def detect_spec_intent(question: str, catalog: Dict[str, set]) -> tuple[bool, str | None, str | None]:
    """
    '쏘나타 알려줘', '카니발 스펙'처럼 스펙 의도면 True와 함께
    brand_like / model_like(부분일치 키워드) 반환.
    - '대수/점유율/상위/추이/합계' 등 집계 단어가 섞이면 False.
    """
    txt = question.lower()

    # 집계 의도 신호어가 있으면 스펙 모드 해제
    agg_words = ["대수", "점유율", "비율", "상위", "top", "추이", "증감", "합계", "총"]
    if any(w in txt for w in agg_words):
        return False, None, None

    # 스펙/정보 의도 신호어
    spec_words = ["알려줘", "정보", "스펙", "자세히", "어떤", "무슨"]
    if not any(w in txt for w in spec_words):
        return False, None, None

    # 카탈로그에서 브랜드/모델 후보 추출(부분일치)
    brand_like = _find_value_in_text(question, catalog.get("brands", set()))
    model_like = _find_value_in_text(question, catalog.get("models", set()))

    if brand_like or model_like:
        return True, brand_like, model_like
    return False, None, None
# ============ 차트/표시 ============

def make_chart(df_out: pd.DataFrame):
    if df_out.shape[0] <= 1: return None
    if df_out.shape[0] <= 8: return px.pie(df_out, values="대수", names="구분", hole=.3)
    return px.bar(df_out, x="구분", y="대수")

def render_condition_summary(meta: dict) -> str:
    src = meta.get("source","")
    group = DISPLAY_NAME.get(meta.get("group",""), meta.get("group",""))
    fs = []
    for f in meta.get("filters", []):
        key = DISPLAY_NAME.get(f.get("key"), f.get("key"))
        val = f.get("display_val") or f.get("val")
        fs.append(f"{key}={val}")
    filt_str = ", ".join(fs) if fs else "없음"
    sort = "오름차순" if meta.get("sort")=="asc" else "내림차순"
    topn = meta.get("topn"); topn_str = f"{topn}" if topn else "해당 없음"
    rb, ra, s = meta.get("rows_before"), meta.get("rows_after"), meta.get("sum_after")
    data_line = f"- 데이터: 적용 전 {rb:,} → 적용 후 {ra:,} (합계 {int(s):,}대)\n" if rb is not None else ""
    return (f"**적용 조건**\n"
            f"- 데이터 소스: {src}\n"
            f"- 그룹 기준: {group}\n"
            f"- 필터: {filt_str}\n"
            f"- 정렬: {sort} | 상위 N: {topn_str}\n"
            f"{data_line}")

# ============ LLM 설명(유도값 허용) ============

def llm_explain(plan: Dict[str, Any], df_out: pd.DataFrame, question: str, api_key: str,
                system_prompt: Optional[str] = None, model: str = "gpt-3.5-turbo") -> str:
    """
    - '가상의 수치' 생성 금지
    - df_out에 존재하는 값으로부터의 비율(%), 평균, 점유율 등 '유도값' 계산은 허용
    """
    if not api_key: return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        sys = system_prompt or (
            "너는 차량 등록 통계를 설명하는 데이터 분석가다. "
            "오직 내가 제공하는 표(df_out)의 값만을 근거로 설명한다. "
            "숫자를 새로 '추정/창작'하지 말고, 표의 값으로부터 파생된 비율(%), 평균, 점유율, 단순 합/차 등은 계산해도 된다. "
            "근거가 되는 수치(분모/분자)를 함께 언급하라. 핵심 2~5문장, 불릿 금지."
        )
        payload = {
            "question": question,
            "plan": plan,
            "stats": df_out.to_dict(orient="records"),
        }
        res = client.chat.completions.create(
            model=model, temperature=0.2,
            messages=[{"role":"system","content":sys},
                      {"role":"user","content":json.dumps(payload, ensure_ascii=False)}]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"(LLM 설명 오류) {e}"
