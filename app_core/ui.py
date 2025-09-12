from typing import Dict, Any, Tuple, Iterable, Optional
import streamlit as st

def section(title: str, subtitle: Optional[str] = None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)

def columns(n_or_weights: Iterable[int]) -> Tuple[st.delta_generator.DeltaGenerator, ...]:
    return st.columns(n_or_weights)

def sidebar_filters(schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    schema 예:
    {
      "brand": {"type":"multiselect","label":"브랜드","options":[...], "default": None},
      "fuel":  {"type":"selectbox","label":"연료","options":["전체", ...], "default":"전체"},
    }
    """
    out = {}
    with st.sidebar:
        st.markdown("#### 필터")
        for key, cfg in schema.items():
            typ = cfg["type"]
            label = cfg.get("label", key)
            options = cfg.get("options", [])
            default = cfg.get("default", None)
            if typ == "multiselect":
                val = st.multiselect(label, options, default=default)
            elif typ == "selectbox":
                val = st.selectbox(label, options, index=(options.index(default) if default in options else 0))
            elif typ == "radio":
                val = st.radio(label, options, index=(options.index(default) if default in options else 0), horizontal=True)
            else:
                val = None
            out[key] = val
    return out

def compare_form(schema: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Overview 비교/증감 분석 폼 패턴
    schema 예:
    {"target": {"type":"radio","label":"대상","options":["신규","이전","말소"],"default":"신규"},
     "key": {"type":"selectbox","label":"기준","options":["브랜드","모델","연료"],"default":"브랜드"}}
    """
    with st.form(key="compare_form"):
        st.markdown("#### 비교/증감 분석")
        result = {}
        for key, cfg in schema.items():
            typ = cfg["type"]
            label = cfg.get("label", key)
            options = cfg.get("options", [])
            default = cfg.get("default", None)
            if typ == "selectbox":
                result[key] = st.selectbox(label, options, index=(options.index(default) if default in options else 0))
            elif typ == "radio":
                result[key] = st.radio(label, options, index=(options.index(default) if default in options else 0), horizontal=True)
            else:
                result[key] = None
        submitted = st.form_submit_button("분석 실행")
        if submitted:
            return result
    return None