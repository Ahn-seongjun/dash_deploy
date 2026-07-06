from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app_core import data_loader as dl


MARTS_DIR = Path("data") / "marts"
DEFAULT_HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"

SOURCE_LABELS = {
    "newreg": "신규등록",
    "usedreg": "이전등록",
    "erase": "말소등록",
    "car_use": "용도연도집계",
}

DIMENSION_LABELS = {
    "month": "월",
    "brand": "브랜드",
    "fuel": "연료",
    "body": "차형",
    "size": "차급",
    "region": "지역",
    "origin": "국산/수입",
    "age": "연령대",
    "car_use": "용도",
}


def _safe_str(value: Any) -> str:
    if pd.isna(value):
        return "-"
    text = str(value).strip()
    return text if text else "-"


def _month_label(value: Any) -> str:
    text = re.sub(r"\D", "", _safe_str(value))
    if len(text) == 6:
        return f"{text[:4]}-{text[4:]}"
    return _safe_str(value)


def _parse_month_from_question(question: str) -> str | None:
    match = re.search(r"(20\d{2})[.\-/년 ]?(0?[1-9]|1[0-2])", question)
    if not match:
        return None
    year = match.group(1)
    month = int(match.group(2))
    return f"{year}-{month:02d}"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[0-9]+|[가-힣A-Za-z]+", text.lower())


def _keyword_score(question_tokens: set[str], text: str) -> float:
    doc_tokens = _tokenize(text)
    if not doc_tokens:
        return 0.0
    overlap = sum(1 for token in doc_tokens if token in question_tokens)
    if overlap == 0:
        return 0.0
    return overlap / math.sqrt(max(len(set(doc_tokens)), 1))


def detect_source_from_question(question: str) -> str | None:
    q = question.lower().replace(" ", "")
    if any(keyword in q for keyword in ["신차", "신규", "신규등록", "신차등록"]):
        return "newreg"
    if any(keyword in q for keyword in ["이전", "이전등록", "중고"]):
        return "usedreg"
    if any(keyword in q for keyword in ["말소", "폐차"]):
        return "erase"
    if any(keyword in q for keyword in ["용도", "용도별"]):
        return "car_use"
    return None


def is_total_count_question(question: str) -> bool:
    q = question.lower().replace(" ", "")
    return any(
        keyword in q
        for keyword in ["대수", "몇대", "총등록", "등록대수", "전체등록", "전체대수", "월등록"]
    )


def _read_mart(name: str, columns: list[str] | None = None) -> pd.DataFrame:
    return dl.load_parquet(MARTS_DIR / name, columns=columns)


def _normalize_detail(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "CNT" not in out.columns:
        out["CNT"] = 1
    out["CNT"] = pd.to_numeric(out["CNT"], errors="coerce").fillna(0).astype(int)
    if "EXTRACT_DE" in out.columns:
        out["EXTRACT_DE"] = pd.to_numeric(out["EXTRACT_DE"], errors="coerce").fillna(0).astype(int)
        out["MONTH"] = out["EXTRACT_DE"].astype(str).str.zfill(6).str[:6]
    return out


def _append_docs(
    docs: list[dict[str, Any]],
    grouped: pd.DataFrame,
    source_key: str,
    dimension_key: str,
    label_col: str,
    month_col: str = "MONTH",
) -> None:
    for row in grouped.itertuples(index=False):
        month_text = _month_label(getattr(row, month_col, None))
        label_text = _safe_str(getattr(row, label_col, None))
        count_value = int(getattr(row, "CNT", 0))
        docs.append(
            {
                "source": source_key,
                "source_label": SOURCE_LABELS[source_key],
                "month": month_text,
                "dimension": dimension_key,
                "dimension_label": DIMENSION_LABELS[dimension_key],
                "label": label_text,
                "value": count_value,
                "text": f"{SOURCE_LABELS[source_key]} 데이터에서 {month_text} {DIMENSION_LABELS[dimension_key]} {label_text} 등록대수는 {count_value:,}대입니다.",
            }
        )


def _build_detail_docs(df: pd.DataFrame, source_key: str) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    out = _normalize_detail(df)
    if out.empty or "MONTH" not in out.columns:
        return docs

    monthly = out.groupby("MONTH", as_index=False, dropna=False)["CNT"].sum()
    for row in monthly.itertuples(index=False):
        month_text = _month_label(row.MONTH)
        count_value = int(row.CNT)
        docs.append(
            {
                "source": source_key,
                "source_label": SOURCE_LABELS[source_key],
                "month": month_text,
                "dimension": "month",
                "dimension_label": "월",
                "label": month_text,
                "value": count_value,
                "text": f"{SOURCE_LABELS[source_key]} 데이터에서 {month_text} 전체 등록대수는 {count_value:,}대입니다.",
            }
        )

    dim_map = {
        "ORG_CAR_MAKER_KOR": "brand",
        "USE_FUEL_NM": "fuel",
        "CAR_BT": "body",
        "CAR_SZ": "size",
        "JUSO_SIDO": "region",
        "CL_HMMD_IMP_SE_NM": "origin",
        "SOU_AGE": "age",
    }
    for col, dim_key in dim_map.items():
        if col not in out.columns:
            continue
        grouped = (
            out.groupby(["MONTH", col], as_index=False, dropna=False)["CNT"]
            .sum()
            .sort_values(["MONTH", "CNT"], ascending=[True, False])
        )
        grouped = grouped.groupby("MONTH", group_keys=False).head(12).reset_index(drop=True)
        _append_docs(docs, grouped, source_key, dim_key, col)

    return docs


def _build_car_use_docs(df: pd.DataFrame) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    if df.empty:
        return docs

    work = df.copy()
    if "YEAR" not in work.columns:
        year_cols = [col for col in work.columns if str(col).isdigit()]
        if year_cols:
            work = work.melt(
                id_vars=[col for col in ["CAR_USE", "CAR_USE_DETAL"] if col in work.columns],
                value_vars=year_cols,
                var_name="YEAR",
                value_name="CNT",
            )

    work["YEAR"] = pd.to_numeric(work["YEAR"], errors="coerce")
    work["CNT"] = pd.to_numeric(work["CNT"], errors="coerce").fillna(0).astype(int)
    work = work.dropna(subset=["YEAR"])
    if work.empty:
        return docs

    grouped = (
        work.groupby(["YEAR", "CAR_USE"], as_index=False, dropna=False)["CNT"]
        .sum()
        .sort_values(["YEAR", "CNT"], ascending=[True, False])
    )
    grouped = grouped.groupby("YEAR", group_keys=False).head(10).reset_index(drop=True)
    for row in grouped.itertuples(index=False):
        year_text = str(int(row.YEAR))
        label_text = _safe_str(row.CAR_USE)
        count_value = int(row.CNT)
        docs.append(
            {
                "source": "car_use",
                "source_label": SOURCE_LABELS["car_use"],
                "month": year_text,
                "dimension": "car_use",
                "dimension_label": "용도",
                "label": label_text,
                "value": count_value,
                "text": f"용도연도집계 데이터에서 {year_text}년 용도 {label_text} 등록대수는 {count_value:,}대입니다.",
            }
        )
    return docs


@st.cache_data(ttl=3600, show_spinner="RAG 문서를 준비하는 중입니다...")
def load_rag_documents() -> pd.DataFrame:
    docs: list[dict[str, Any]] = []
    docs.extend(_build_detail_docs(_read_mart("newreg_detail.parquet"), "newreg"))
    docs.extend(_build_detail_docs(_read_mart("used_detail.parquet"), "usedreg"))
    docs.extend(_build_detail_docs(_read_mart("erase_detail.parquet"), "erase"))
    docs.extend(_build_car_use_docs(_read_mart("car_use_yearly_summary.parquet")))
    return pd.DataFrame(docs)


def dataset_options(doc_df: pd.DataFrame) -> list[str]:
    labels = ["전체"]
    for key in ["newreg", "usedreg", "erase", "car_use"]:
        if key in set(doc_df["source"].astype(str)):
            labels.append(SOURCE_LABELS[key])
    return labels


def answer_direct_count(question: str, doc_df: pd.DataFrame) -> tuple[pd.DataFrame, str] | None:
    source_key = detect_source_from_question(question)
    month_label = _parse_month_from_question(question)
    if source_key is None or month_label is None or not is_total_count_question(question):
        return None

    matched = doc_df[
        (doc_df["source"] == source_key)
        & (doc_df["dimension"] == "month")
        & (doc_df["month"] == month_label)
    ].copy()
    if matched.empty:
        return None

    matched = matched.sort_values("value", ascending=False).reset_index(drop=True)
    value = int(matched.iloc[0]["value"])
    answer = f"{SOURCE_LABELS[source_key]} 기준 {month_label} 등록대수는 {value:,}대입니다."
    return matched, answer


def retrieve_documents(
    question: str,
    doc_df: pd.DataFrame,
    source_label: str = "전체",
    top_k: int = 8,
) -> pd.DataFrame:
    if doc_df.empty:
        return doc_df.copy()

    filtered = doc_df.copy()
    forced_source = detect_source_from_question(question)

    if source_label != "전체":
        source_key = next((k for k, v in SOURCE_LABELS.items() if v == source_label), None)
        if source_key:
            filtered = filtered[filtered["source"] == source_key]
    elif forced_source is not None:
        filtered = filtered[filtered["source"] == forced_source]

    q_tokens = set(_tokenize(question))
    if not q_tokens:
        q_tokens = {question.lower()}

    scored = filtered.copy()
    scored["score"] = scored["text"].map(lambda text: _keyword_score(q_tokens, text))

    month_label = _parse_month_from_question(question)
    if month_label is not None:
        scored.loc[scored["month"] == month_label, "score"] += 3.0

    if forced_source is not None:
        scored.loc[scored["source"] == forced_source, "score"] += 4.0

    if is_total_count_question(question):
        scored.loc[scored["dimension"] == "month", "score"] += 3.0

    if any(keyword in question for keyword in ["브랜드", "제조사"]):
        scored.loc[scored["dimension"] == "brand", "score"] += 2.0
    if any(keyword in question for keyword in ["연료", "하이브리드", "전기", "휘발유", "경유", "LPG", "lpg"]):
        scored.loc[scored["dimension"] == "fuel", "score"] += 2.0
    if any(keyword in question for keyword in ["지역", "시도", "서울", "경기", "부산", "인천"]):
        scored.loc[scored["dimension"] == "region", "score"] += 2.0

    if not scored["score"].gt(0).any():
        return scored.sort_values(["month", "value"], ascending=[False, False]).head(top_k).reset_index(drop=True)

    return scored.sort_values(["score", "value"], ascending=[False, False]).head(top_k).reset_index(drop=True)


def build_context_block(retrieved_df: pd.DataFrame) -> str:
    if retrieved_df.empty:
        return "검색된 근거 문서가 없습니다."
    return "\n".join(f"{idx}. {row.text}" for idx, row in enumerate(retrieved_df.itertuples(index=False), start=1))


def build_fallback_answer(question: str, retrieved_df: pd.DataFrame) -> str:
    if retrieved_df.empty:
        return "관련 근거를 찾지 못했습니다. 질문에 월, 등록구분, 브랜드, 연료 같은 조건을 더 넣어주세요."

    top = retrieved_df.iloc[0]
    if top["dimension"] == "month":
        return f"{top['source_label']} 기준 {top['month']} 등록대수는 {int(top['value']):,}대입니다."

    same_group = retrieved_df[
        (retrieved_df["source"] == top["source"])
        & (retrieved_df["dimension"] == top["dimension"])
        & (retrieved_df["month"] == top["month"])
    ].copy()
    same_group = same_group.sort_values("value", ascending=False)

    message = f"{top['source_label']} 기준 가장 직접적인 근거는 '{top['text']}'입니다."
    if len(same_group) > 1:
        leader = same_group.iloc[0]
        total = int(same_group["value"].sum())
        share = (int(leader["value"]) / total * 100) if total else 0.0
        message += f" 같은 기준 내에서는 {leader['dimension_label']} '{leader['label']}'가 {int(leader['value']):,}대로 가장 크고 비중은 {share:.1f}%입니다."
    return message


def answer_with_huggingface(
    question: str,
    retrieved_df: pd.DataFrame,
    api_token: str,
    model_name: str = DEFAULT_HF_MODEL,
) -> str:
    if not api_token:
        return build_fallback_answer(question, retrieved_df)

    context_block = build_context_block(retrieved_df)
    system_prompt = (
        "당신은 자동차 등록 데이터 분석 도우미다. "
        "반드시 제공된 근거 문장만 사용해 답하고, 근거에 없는 수치는 추정하지 마라. "
        "답변은 한국어 3~5문장으로 간결하게 작성하라."
    )
    user_prompt = (
        f"[질문]\n{question}\n\n"
        f"[근거 문서]\n{context_block}\n\n"
        "[작성 규칙]\n"
        "- 근거 문서에 있는 숫자만 사용\n"
        "- 비교 시 기준을 분명히 명시\n"
        "- 마지막 줄에 '근거: ...' 형식으로 핵심 기준 첨부"
    )

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(api_key=api_token)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"{build_fallback_answer(question, retrieved_df)}\n\n(Hugging Face 호출 오류: {exc})"
