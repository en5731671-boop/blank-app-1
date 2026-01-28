import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# Supabase 接続（KeyError防止）
# =========================

# st.secrets が正しく登録されているか確認
if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
    st.error("SupabaseのSecretsが登録されていません。SUPABASE_URLとSUPABASE_KEYを登録してください。")
    st.stop()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# =========================
# ページ設定
# =========================
st.set_page_config(page_title="学習リフレクションアプリ", layout="wide")
st.title("📘 学習リフレクション・ログアプリ")
st.caption("学習の「量」と「理解度」を同時に記録・可視化します")

# =========================
# 学習ログ追加フォーム
# =========================
st.header("➕ 学習ログを追加")

with st.form("study_form"):
    task_name = st.text_input("学習内容（例：RSA暗号の復習）")
    subject = st.text_input("科目名")
    study_minutes = st.number_input("学習時間（分）", 0, step=10)
    understanding = st.slider("理解度（1：難しい〜5：よく理解できた）", 1, 5, 3)
    reflection = st.text_area("振り返り・気づき")
    submitted = st.form_submit_button("記録する")

if submitted:
    if not task_name:
        st.warning("タスク名を入力してください")
    else:
        supabase.table("study_logs").insert({
            "task_name": task_name,
            "subject": subject,
            "study_minutes": study_minutes,
            "understanding": understanding,
            "reflection": reflection
        }).execute()
        st.success("学習ログを保存しました！")
        st.experimental_rerun()  # 保存後に更新

# =========================
# 学習ログ取得
# =========================
response = supabase.table("study_logs").select("*").order("created_at").execute()
data = response.data

if not data:
    st.info("まだ学習ログがありません")
    st.stop()

df = pd.DataFrame(data)

# =========================
# 学習ログ一覧表示
# =========================
st.header("📋 学習ログ一覧")

for _, row in df.iterrows():
    with st.expander(f"📌 {row['task_name']}（{row['subject']}）"):
        st.write(f"⏱ 学習時間：{row['study_minutes']} 分")
        st.write(f"⭐ 理解度：{row['understanding']} / 5")
        st.write("📝 振り返り")
        st.write(row["reflection"] if row["reflection"] else "（記入なし）")

# =========================
# 分析・可視化
# =========================
st.header("📊 学習のふりかえり分析")

col1, col2 = st.columns(2)
with col1:
    total_time = df["study_minutes"].sum()
    st.metric("総学習時間", f"{total_time} 分")
with col2:
    avg_understanding = round(df["understanding"].mean(), 2)
    st.metric("平均理解度", avg_understanding)

st.subheader("理解度 × 学習時間")
st.scatter_chart(df[["study_minutes", "understanding"]])

st.subheader("科目別 学習時間")
subject_sum = df.groupby("subject")["study_minutes"].sum()
st.bar_chart(subject_sum)

# =========================
# ログ削除機能
# =========================
st.header("🗑️ 学習ログ削除")
for _, row in df.iterrows():
    if st.button(f"削除: {row['task_name']} ({row['subject']})", key=row['id']):
        supabase.table("study_logs").delete().eq("id", row['id']).execute()
        st.success(f"{row['task_name']} を削除しました")
        st.experimental_rerun()
