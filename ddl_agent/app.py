import streamlit as st
from datetime import datetime, timedelta
import json
import os

# 页面标题
st.set_page_config(page_title="DDL智能管家", page_icon="📚")
st.title("📚 学习DDL与资料管理智能体")
st.caption("中兴赛道命题四 | 南京理工大学")

# 数据文件
DATA_FILE = "ddl_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 加载数据
if "ddl_list" not in st.session_state:
    st.session_state.ddl_list = load_data()

# ========== 左侧：添加任务 ==========
with st.sidebar:
    st.header("➕ 添加新任务")
    
    course = st.text_input("课程名称", placeholder="例如：数据结构")
    task = st.text_input("任务名称", placeholder="例如：第三章作业")
    ddl_date = st.date_input("截止日期", value=datetime.now() + timedelta(days=7))
    ddl_time = st.time_input("截止时间", value=datetime.strptime("23:59", "%H:%M").time())
    submit = st.text_input("提交方式", placeholder="例如：智慧理工平台")
    note = st.text_area("备注", placeholder="命名格式等...")
    
    if st.button("💾 保存", type="primary", use_container_width=True):
        if course and task:
            new_item = {
                "id": len(st.session_state.ddl_list),
                "课程": course,
                "任务": task,
                "截止时间": f"{ddl_date} {ddl_time.strftime('%H:%M')}",
                "提交方式": submit or "未填写",
                "备注": note or "无",
                "录入时间": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.ddl_list.append(new_item)
            save_data(st.session_state.ddl_list)
            st.success("✅ 添加成功！")
            st.rerun()
        else:
            st.error("❌ 课程和任务名称不能为空")

# ========== 中间：展示任务 ==========
st.header("📋 我的任务清单")

if not st.session_state.ddl_list:
    st.info("暂无任务，请从左侧添加")
else:
    for idx, item in enumerate(st.session_state.ddl_list):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**📌 {item['课程']} - {item['任务']}**")
                st.write(f"⏰ 截止时间：{item['截止时间']}")
                st.write(f"📤 提交方式：{item['提交方式']}")
                if item['备注'] != "无":
                    st.write(f"💬 备注：{item['备注']}")
            
            with col2:
                # 计算剩余天数
                try:
                    ddl = datetime.strptime(item['截止时间'], "%Y-%m-%d %H:%M")
                    days = (ddl - datetime.now()).days
                    if days < 0:
                        st.error("已逾期")
                    elif days <= 3:
                        st.warning(f"剩{days}天")
                    else:
                        st.success(f"剩{days}天")
                except:
                    st.write("时间未知")
                
                if st.button("删除", key=f"del_{idx}"):
                    st.session_state.ddl_list.pop(idx)
                    save_data(st.session_state.ddl_list)
                    st.rerun()

# ========== 底部：导出 ==========
st.divider()
st.header("💾 导出数据")

if st.session_state.ddl_list:
    # JSON
    json_str = json.dumps(st.session_state.ddl_list, ensure_ascii=False, indent=2)
    st.download_button("📥 导出JSON", data=json_str, file_name="DDL.json", mime="application/json")
    
    # CSV
    csv = "课程,任务,截止时间,提交方式,备注\n"
    for item in st.session_state.ddl_list:
        csv += f"{item['课程']},{item['任务']},{item['截止时间']},{item['提交方式']},{item['备注']}\n"
    st.download_button("📥 导出CSV", data=csv, file_name="DDL.csv", mime="text/csv")
    
    # 日历
    ical = "BEGIN:VCALENDAR\nVERSION:2.0\n"
    for item in st.session_state.ddl_list:
        try:
            ddl = datetime.strptime(item['截止时间'], "%Y-%m-%d %H:%M")
            dt = ddl.strftime("%Y%m%dT%H%M%S")
            ical += f"BEGIN:VEVENT\nDTSTART:{dt}\nSUMMARY:{item['课程']}-{item['任务']}\nEND:VEVENT\n"
        except:
            pass
    ical += "END:VCALENDAR"
    st.download_button("📅 导出日历(.ics)", data=ical, file_name="DDL.ics", mime="text/calendar")
    
    if st.button("🗑️ 清空所有"):
        st.session_state.ddl_list = []
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.rerun()