from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "warehouse.duckdb"

ISSUE_KEYWORDS = [
    "픽셀",
    "CTA",
    "A/B",
    "캠페인",
    "컨펌",
    "누끼",
    "비주얼",
    "카피",
    "전환",
    "Slack",
    "Google Analytics",
]


st.set_page_config(page_title="Meeting Action Dashboard", layout="wide")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame()

    with duckdb.connect(DB_PATH) as conn:
        meetings = conn.sql(
            """
            SELECT
                meeting_id,
                advertiser,
                campaign,
                meeting_date,
                source_type,
                created_at
            FROM meetings
            """
        ).df()
        action_items = conn.sql(
            """
            SELECT
                action_item_id,
                meeting_id,
                chunk_id,
                owner,
                task,
                due_date,
                priority,
                status,
                confidence,
                source_utterance,
                reasoning,
                created_at
            FROM action_items
            """
        ).df()

    if not meetings.empty:
        meetings["meeting_date"] = pd.to_datetime(meetings["meeting_date"])
        meetings["week"] = meetings["meeting_date"].dt.to_period("W").astype(str)

    if not action_items.empty:
        action_items["created_at"] = pd.to_datetime(action_items["created_at"])

    return meetings, action_items


def build_keyword_counts(meetings: pd.DataFrame, action_items: pd.DataFrame) -> pd.DataFrame:
    if meetings.empty or action_items.empty:
        return pd.DataFrame(columns=["advertiser", "campaign", "keyword", "count"])

    merged = action_items.merge(
        meetings[["meeting_id", "advertiser", "campaign"]],
        on="meeting_id",
        how="left",
    )
    rows = []

    for _, row in merged.iterrows():
        haystack = f"{row['task']} {row['source_utterance']}"
        for keyword in ISSUE_KEYWORDS:
            if keyword.lower() in haystack.lower():
                rows.append(
                    {
                        "advertiser": row["advertiser"],
                        "campaign": row["campaign"],
                        "keyword": keyword,
                        "count": 1,
                    }
                )

    if not rows:
        return pd.DataFrame(columns=["advertiser", "campaign", "keyword", "count"])

    return (
        pd.DataFrame(rows)
        .groupby(["advertiser", "campaign", "keyword"], as_index=False)["count"]
        .sum()
        .sort_values("count", ascending=False)
    )


def render_empty_state() -> None:
    st.warning("데이터가 없습니다. 먼저 `make run`을 실행해 DuckDB와 processed JSON을 생성해주세요.")


def main() -> None:
    st.title("Meeting Action Dashboard")
    st.caption("회의 transcript에서 추출한 액션아이템과 신뢰도 신호를 한 화면에서 검토합니다.")

    meetings, action_items = load_data()

    if meetings.empty or action_items.empty:
        render_empty_state()
        return

    total_meetings = len(meetings)
    total_actions = len(action_items)
    open_actions = int((action_items["status"] != "done").sum())
    avg_confidence = float(action_items["confidence"].mean())

    metric_cols = st.columns(4)
    metric_cols[0].metric("회의 수", f"{total_meetings}")
    metric_cols[1].metric("액션아이템", f"{total_actions}")
    metric_cols[2].metric("미완료", f"{open_actions}")
    metric_cols[3].metric("평균 confidence", f"{avg_confidence:.2f}")

    st.divider()

    weekly = meetings[["meeting_id", "week"]].merge(
        action_items[["meeting_id", "action_item_id"]],
        on="meeting_id",
        how="left",
    )
    weekly_summary = (
        weekly.groupby("week", as_index=False)
        .agg(
            meetings=("meeting_id", "nunique"),
            action_items=("action_item_id", "count"),
        )
        .set_index("week")
    )

    st.subheader("주차별 회의·액션아이템 발생 추이")
    st.line_chart(weekly_summary)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("담당자별 미완료 액션아이템 Top N")
        owner_summary = (
            action_items[action_items["status"] != "done"]
            .groupby("owner", as_index=False)
            .agg(open_action_items=("action_item_id", "count"))
            .sort_values("open_action_items", ascending=False)
        )
        st.bar_chart(owner_summary.set_index("owner"))
        st.dataframe(
            action_items[
                ["owner", "task", "due_date", "priority", "status", "confidence"]
            ].sort_values(["owner", "priority"]),
            use_container_width=True,
            hide_index=True,
        )

    with col_right:
        st.subheader("캠페인 / 광고주별 반복 이슈 키워드")
        keyword_counts = build_keyword_counts(meetings, action_items)
        if keyword_counts.empty:
            st.info("반복 이슈 키워드가 감지되지 않았습니다.")
        else:
            st.bar_chart(keyword_counts.set_index("keyword")["count"])
            st.dataframe(keyword_counts, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("LLM 추출 confidence 분포 + 낮은 항목 드릴다운")
    confidence_cols = st.columns([1, 1])

    with confidence_cols[0]:
        bins = pd.cut(
            action_items["confidence"],
            bins=[0.0, 0.75, 0.85, 0.95, 1.0],
            labels=["0.00-0.75", "0.75-0.85", "0.85-0.95", "0.95-1.00"],
            include_lowest=True,
        )
        confidence_distribution = (
            action_items.assign(confidence_bin=bins)
            .groupby("confidence_bin", observed=False)
            .size()
            .reset_index(name="count")
            .set_index("confidence_bin")
        )
        st.bar_chart(confidence_distribution)

    with confidence_cols[1]:
        threshold = st.slider(
            "낮은 confidence 기준",
            min_value=0.0,
            max_value=1.0,
            value=0.85,
            step=0.05,
        )
        low_confidence = action_items[action_items["confidence"] <= threshold]
        st.dataframe(
            low_confidence[
                [
                    "owner",
                    "task",
                    "due_date",
                    "confidence",
                    "source_utterance",
                    "reasoning",
                ]
            ].sort_values("confidence"),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
