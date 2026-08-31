import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client
import json
import requests
import base64

# ========== 配置区（只改这里） ==========
SUPABASE_URL = "https://ajugxvdbknwaoxxkswmo.supabase.co"
SUPABASE_KEY = "sb_publishable_riUdW2EgE5AQCVMMV1M_yQ_RSpjmHy9"
ZHIPU_KEY = "sk-46024e696b404c35a273f44003583eda.lE37ReQGD9atrxhm"  

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 页面设置 ==========
st.set_page_config(page_title="DDL智能管家", page_icon="📚")
st.title("📚 学习DDL与资料管理智能体")
st.caption("中兴赛道命题四 | 南京理工大学 | AI识别版")

# ========== 用户登录 ==========
st.sidebar.header("👤 用户身份")

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

current_user = st.sidebar.text_input(
    "输入你的名字（只能看到自己的任务）",
    value=st.session_state.current_user,
    placeholder="例如：张三"
)

if current_user:
    st.session_state.current_user = current_user
    st.sidebar.success(f"当前用户：{current_user}")
else:
    st.sidebar.warning("⚠️ 请先输入名字才能使用")
    st.stop()

# ========== 数据库操作 ==========
def load_data(user):
    try:
        response = supabase.table('tasks')\
            .select('*')\
            .eq('用户名', user)\
            .order('截止时间')\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"读取失败：{e}")
        return []

def add_task_db(user, course, task, ddl, submit, note):
    try:
        data = {
            "用户名": user,
            "课程": course,
            "任务": task,
            "截止时间": ddl,
            "提交方式": submit or "未填写",
            "备注": note or "无",
            "录入时间": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        supabase.table('tasks').insert(data).execute()
    except Exception as e:
        st.error(f"保存失败：{e}")

def delete_task_db(user, task_id):
    try:
        supabase.table('tasks')\
            .delete()\
            .eq('id', task_id)\
            .eq('用户名', user)\
            .execute()
    except Exception as e:
        st.error(f"删除失败：{e}")

def clear_all_db(user):
    try:
        supabase.table('tasks')\
            .delete()\
            .eq('用户名', user)\
            .execute()
    except Exception as e:
        st.error(f"清空失败：{e}")

# ========== AI提取函数（文字版） ==========
def extract_with_ai(text):
    if ZHIPU_KEY == "sk-你的智谱APIKey":
        return None, "请先填写智谱API Key"
    
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""请从以下课程通知中提取关键信息，以JSON格式返回：
{text}

要求提取：
- 课程名称
- 任务名称
- 截止时间（格式：YYYY-MM-DD HH:MM，如果只有日期，时间默认23:59）
- 提交方式
- 备注（命名格式、特殊要求等，没有则填"无"）

只返回JSON，不要其他文字。格式：
{{"课程名称":"...","任务名称":"...","截止时间":"...","提交方式":"...","备注":"..."}}"""
    
    try:
        response = requests.post(url, headers=headers, json={
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }, timeout=15)
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 清理markdown格式
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        data = json.loads(content.strip())
        return data, None
    except Exception as e:
        return None, str(e)

# ========== AI提取函数（图片版） ==========
def extract_with_image(image_bytes):
    if ZHIPU_KEY == "sk-你的智谱APIKey":
        return None, "请先填写智谱API Key"
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """这是一张课程通知的截图。请识别图中的文字，并提取以下信息，以JSON格式返回：
- 课程名称
- 任务名称
- 截止时间（格式：YYYY-MM-DD HH:MM，如果只有日期，时间默认23:59）
- 提交方式
- 备注（命名格式、特殊要求等，没有则填"无"）

只返回JSON，不要其他文字。格式：
{"课程名称":"...","任务名称":"...","截止时间":"...","提交方式":"...","备注":"..."}"""
    
    try:
        response = requests.post(url, headers=headers, json={
            "model": "glm-4v-flash",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            "temperature": 0.1
        }, timeout=20)
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 清理markdown格式
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        data = json.loads(content.strip())
        return data, None
    except Exception as e:
        return None, str(e)

# ========== 保存AI提取结果的通用函数 ==========
def save_extracted_data(user, data):
    ddl_str = data.get("截止时间", "")
    try:
        ddl_dt = datetime.strptime(ddl_str, "%Y-%m-%d %H:%M")
    except:
        try:
            ddl_dt = datetime.strptime(ddl_str, "%Y-%m-%d")
            ddl_dt = ddl_dt.replace(hour=23, minute=59)
        except:
            ddl_dt = datetime.now() + timedelta(days=7)
    
    add_task_db(
        user,
        data.get("课程名称", "未识别"),
        data.get("任务名称", "未识别"),
        ddl_dt.strftime("%Y-%m-%d %H:%M"),
        data.get("提交方式", "未明确"),
        data.get("备注", "无")
    )

# ========== 加载数据 ==========
if "ddl_list" not in st.session_state:
    st.session_state.ddl_list = []

st.session_state.ddl_list = load_data(current_user)

# ========== 🔔 提醒中心 ==========
st.header("🔔 提醒中心")

now = datetime.now()
tasks = st.session_state.ddl_list

overdue = []
today = []
tomorrow = []
week = []

for item in tasks:
    try:
        ddl = datetime.strptime(item['截止时间'], '%Y-%m-%d %H:%M')
        delta = (ddl - now).days
        if delta < 0:
            overdue.append(item)
        elif delta == 0:
            today.append(item)
        elif delta == 1:
            tomorrow.append(item)
        elif 2 <= delta <= 7:
            week.append(item)
    except:
        pass

if overdue or today or tomorrow:
    cols = st.columns(3)
    
    with cols[0]:
        if overdue:
            with st.container(border=True):
                st.error(f"🔴 已逾期 {len(overdue)} 个")
                for item in overdue:
                    st.write(f"**{item['课程']}** - {item['任务']}")
    
    with cols[1]:
        if today:
            with st.container(border=True):
                st.warning(f"🟠 今天截止 {len(today)} 个")
                for item in today:
                    st.write(f"**{item['课程']}** - {item['任务']}")
    
    with cols[2]:
        if tomorrow:
            with st.container(border=True):
                st.info(f"🔵 明天截止 {len(tomorrow)} 个")
                for item in tomorrow:
                    st.write(f"**{item['课程']}** - {item['任务']}")
    
    if week:
        with st.expander(f"📅 未来7天还有 {len(week)} 个任务"):
            for item in week:
                ddl = datetime.strptime(item['截止时间'], '%Y-%m-%d %H:%M')
                st.write(f"**{item['课程']}** - {item['任务']}（{ddl.strftime('%m月%d日')}）")
else:
    st.success("🎉 近期没有紧急任务，可以放松一下！")

st.divider()

# ========== 左侧：添加任务（三种方式） ==========
with st.sidebar:
    st.header("➕ 添加新任务")
    
    # --- 1. AI截图识别 ---
    with st.expander("📸 AI截图识别", expanded=True):
        uploaded_file = st.file_uploader(
            "上传课程通知截图",
            type=["png", "jpg", "jpeg"],
            help="支持微信/QQ截图、手机拍照、网页截图等"
        )
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="已上传的截图", use_container_width=True)
            
            if st.button("🔍 AI识别图片", type="primary", use_container_width=True):
                if ZHIPU_KEY == "sk-你的智谱APIKey":
                    st.error("❌ 请先修改代码中的 ZHIPU_KEY！")
                else:
                    with st.spinner("AI正在看图识字..."):
                        image_bytes = uploaded_file.getvalue()
                        data, err = extract_with_image(image_bytes)
                    
                    if err:
                        st.error(f"识别失败：{err}")
                    elif data:
                        save_extracted_data(current_user, data)
                        st.session_state.ddl_list = load_data(current_user)
                        st.success("✅ 截图识别成功并已保存！")
                        with st.expander("查看识别结果"):
                            st.json(data)
                        st.rerun()
    
    st.divider()
    
    # --- 2. AI文字提取 ---
    with st.expander("📝 粘贴文字通知"):
        notice = st.text_area("粘贴课程通知：", height=100,
            placeholder="例如：各位同学，《数据结构》第三章作业请于9月15日晚8点前提交...")
        
        if st.button("🔍 AI一键提取", use_container_width=True):
            if not notice.strip():
                st.warning("请先粘贴通知内容")
            elif ZHIPU_KEY == "sk-你的智谱APIKey":
                st.error("❌ 请先修改代码中的 ZHIPU_KEY！")
            else:
                with st.spinner("AI正在分析..."):
                    data, err = extract_with_ai(notice)
                
                if err:
                    st.error(f"提取失败：{err}")
                elif data:
                    save_extracted_data(current_user, data)
                    st.session_state.ddl_list = load_data(current_user)
                    st.success("✅ 提取成功并已保存！")
                    with st.expander("查看识别结果"):
                        st.json(data)
                    st.rerun()
    
    st.divider()
    
    # --- 3. 手动录入 ---
    with st.expander("✏️ 手动录入"):
        course = st.text_input("课程名称", placeholder="例如：数据结构", key="m_course")
        task = st.text_input("任务名称", placeholder="例如：第三章作业", key="m_task")
        ddl_date = st.date_input("截止日期", value=datetime.now() + timedelta(days=7), key="m_date")
        ddl_time = st.time_input("截止时间", value=datetime.strptime("23:59", "%H:%M").time(), key="m_time")
        submit = st.text_input("提交方式", placeholder="例如：智慧理工平台", key="m_submit")
        note = st.text_area("备注", placeholder="命名格式等...", key="m_note")
        
        if st.button("💾 手动保存", use_container_width=True):
            if course and task:
                ddl_str = f"{ddl_date} {ddl_time.strftime('%H:%M')}"
                add_task_db(current_user, course, task, ddl_str, submit, note)
                st.session_state.ddl_list = load_data(current_user)
                st.success("✅ 添加成功！")
                st.rerun()
            else:
                st.error("❌ 课程和任务名称不能为空")
    
    # 统计
    st.divider()
    st.header("📊 统计")
    total = len(st.session_state.ddl_list)
    st.metric("总任务数", total)
    
    urgent = len(overdue) + len(today) + len(tomorrow)
    if urgent > 0:
        st.error(f"🔥 紧急任务：{urgent} 个")

# ========== 主区域：任务清单 ==========
st.header(f"📋 {current_user} 的任务清单")

if not st.session_state.ddl_list:
    st.info("暂无任务，请从左侧添加（支持截图识别、文字提取、手动录入三种方式）")
else:
    for idx, item in enumerate(st.session_state.ddl_list):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**📌 {item['课程']} - {item['任务']}**")
                st.write(f"⏰ 截止时间：`{item['截止时间']}`")
                st.write(f"📤 提交方式：{item['提交方式']}")
                if item['备注'] != "无":
                    st.write(f"💬 备注：{item['备注']}")
            
            with col2:
                try:
                    ddl = datetime.strptime(item["截止时间"], "%Y-%m-%d %H:%M")
                    days = (ddl - datetime.now()).days
                    if days < 0:
                        st.error("已逾期")
                    elif days == 0:
                        st.warning("今天截止")
                    elif days == 1:
                        st.info("明天截止")
                    elif days <= 3:
                        st.success(f"剩{days}天")
                    else:
                        st.write(f"剩{days}天")
                except:
                    st.write("时间未知")
                
                if st.button("删除", key=f"del_{item['id']}"):
                    delete_task_db(current_user, item['id'])
                    st.session_state.ddl_list = load_data(current_user)
                    st.rerun()

# ========== 导出区域 ==========
st.divider()
st.header("💾 导出数据")

if st.session_state.ddl_list:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        json_str = json.dumps(st.session_state.ddl_list, ensure_ascii=False, indent=2)
        st.download_button("📥 导出JSON", data=json_str, file_name="DDL.json", mime="application/json")
    
    with col2:
        csv = "课程,任务,截止时间,提交方式,备注\n"
        for item in st.session_state.ddl_list:
            csv += f"{item['课程']},{item['任务']},{item['截止时间']},{item['提交方式']},{item['备注']}\n"
        st.download_button("📥 导出CSV", data=csv, file_name="DDL.csv", mime="text/csv")
    
    with col3:
        ical = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//DDL Agent//CN\n"
        for item in st.session_state.ddl_list:
            try:
                ddl = datetime.strptime(item['截止时间'], "%Y-%m-%d %H:%M")
                dt = ddl.strftime("%Y%m%dT%H%M%S")
                
                ical += f"""BEGIN:VEVENT
DTSTART:{dt}
DTEND:{dt}
SUMMARY:⏰ {item['课程']} - {item['任务']}
DESCRIPTION:提交方式：{item['提交方式']}\\n备注：{item['备注']}
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:任务提醒：{item['课程']} {item['任务']} 即将截止！
TRIGGER:-P1D
END:VALARM
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:紧急提醒：{item['课程']} {item['任务']} 还有1小时截止！
TRIGGER:-PT1H
END:VALARM
END:VEVENT
"""
            except:
                pass
        ical += "END:VCALENDAR"
        st.download_button("📅 导出日历(.ics)", data=ical, file_name="DDL提醒.ics", mime="text/calendar")
        st.caption("💡 导入手机/电脑日历后，提前1天和1小时自动提醒")
    
    if st.button("🗑️ 清空我的所有任务"):
        clear_all_db(current_user)
        st.session_state.ddl_list = []
        st.rerun()