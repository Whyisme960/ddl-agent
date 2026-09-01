import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client
import json
import requests
import base64
import re
import io
import hashlib

# ========== 配置区（只改这里） ==========
SUPABASE_URL = "https://ajugxvdbknwaoxxkswmo.supabase.co"
SUPABASE_KEY = "sb_publishable_riUdW2EgE5AQCVMMV1M_yQ_RSpjmHy9"
ZHIPU_KEY = "sk-46024e696b404c35a273f44003583eda.lE37ReQGD9atrxhm"  

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 密码加密 ==========
def hash_password(password):
    """SHA256加密（加盐）"""
    salt = "ddl-agent-2026-njust"
    return hashlib.sha256((password + salt).encode()).hexdigest()

# ========== 用户认证操作 ==========
def register_user(username, password):
    """注册新用户"""
    try:
        # 检查用户名是否已存在
        existing = supabase.table('users').select('id').eq('username', username).execute()
        if existing.data:
            return False, "用户名已存在，请直接登录"
        
        # 创建用户
        supabase.table('users').insert({
            "username": username,
            "password_hash": hash_password(password),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }).execute()
        return True, "注册成功！请登录"
    except Exception as e:
        return False, f"注册失败：{e}"

def login_user(username, password):
    """验证登录"""
    try:
        response = supabase.table('users')\
            .select('*')\
            .eq('username', username)\
            .eq('password_hash', hash_password(password))\
            .execute()
        
        if response.data:
            return True, "登录成功"
        else:
            return False, "用户名或密码错误"
    except Exception as e:
        return False, f"登录失败：{e}"

# ========== 页面设置 ==========
st.set_page_config(page_title="南理工DDL智能管家", page_icon="📚")
# ========== 南理工风格顶部 ==========
top_col1, top_col2 = st.columns([1, 5])
with top_col1:
    try:
        st.image("njust_logo.png", width=85)
    except:
        # 如果没放图片，显示文字校徽占位
        st.markdown("""
        <div style="width:85px;height:85px;background:linear-gradient(135deg,#4B0082,#8B4513);
        border-radius:50%;display:flex;align-items:center;justify-content:center;
        color:white;font-weight:bold;font-size:12px;text-align:center;">
        南京<br>理工<br>大学
        </div>
        """, unsafe_allow_html=True)

with top_col2:
    st.markdown("""
    <h1 style="margin-bottom:0;color:#4B0082;">
        📚 学习DDL与资料管理智能体
    </h1>
    <p style="margin-top:4px;color:#666;font-size:14px;">
        <b>南京理工大学</b> · 计算机科学与工程学院 · 智能体创新实践大赛
    </p>
    """, unsafe_allow_html=True)

st.divider()
# ========== 登录状态初始化 ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""

# ========== 未登录：显示登录/注册界面 ==========
if not st.session_state.logged_in:
    st.title("📚 学习DDL与资料管理智能体")
    st.caption("中兴赛道命题四 | 南京理工大学 | 安全账号版")
    
    st.info("🔒 请先登录或注册账号，确保您的数据安全私密")
    
    tab1, tab2 = st.tabs(["🔑 登录", "📝 注册"])
    
    with tab1:
        with st.container(border=True):
            st.subheader("登录账号")
            login_name = st.text_input("用户名", placeholder="请输入用户名", key="login_name")
            login_pass = st.text_input("密码", type="password", placeholder="请输入密码", key="login_pass")
            
            if st.button("🔓 登录", type="primary", use_container_width=True):
                if not login_name or not login_pass:
                    st.error("请输入用户名和密码")
                else:
                    success, msg = login_user(login_name, login_pass)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.current_user = login_name
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    with tab2:
        with st.container(border=True):
            st.subheader("注册新账号")
            reg_name = st.text_input("用户名", placeholder="设置一个用户名", key="reg_name")
            reg_pass = st.text_input("密码", type="password", placeholder="设置密码（至少6位）", key="reg_pass")
            reg_pass2 = st.text_input("确认密码", type="password", placeholder="再次输入密码", key="reg_pass2")
            
            if st.button("✅ 注册", type="primary", use_container_width=True):
                if not reg_name or not reg_pass:
                    st.error("用户名和密码不能为空")
                elif len(reg_pass) < 6:
                    st.error("密码至少6位")
                elif reg_pass != reg_pass2:
                    st.error("两次密码不一致")
                else:
                    success, msg = register_user(reg_name, reg_pass)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
    
    st.stop()  # 未登录时，后面的功能全部不显示

# ========== 已登录：显示完整功能 ==========
st.title("📚 学习DDL与资料管理智能体")
st.caption(f"中兴赛道命题四 | 南京理工大学 | 当前用户：{st.session_state.current_user}")

# 退出登录按钮（放在侧边栏顶部）
with st.sidebar:
    if st.button("🚪 退出登录", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.session_state.edit_mode = False
        st.session_state.edit_task = None
        st.rerun()
    
    st.divider()

current_user = st.session_state.current_user

# ========== 编辑状态初始化 ==========
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
    st.session_state.edit_task = None

# ========== 数据库操作（任务表） ==========
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

def update_task_db(task_id, course, task, ddl, submit, note):
    try:
        supabase.table('tasks').update({
            "课程": course,
            "任务": task,
            "截止时间": ddl,
            "提交方式": submit or "未填写",
            "备注": note or "无",
            "录入时间": datetime.now().strftime("%Y-%m-%d %H:%M")
        }).eq('id', task_id).execute()
    except Exception as e:
        st.error(f"更新失败：{e}")

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

# ========== 智能时间解析 ==========
def smart_parse_time(time_str):
    if not time_str or time_str == "未明确":
        return datetime.now() + timedelta(days=7)
    
    s = time_str.strip().replace("：", ":").replace(" ", "")
    
    for fmt in ["%Y-%m-%d%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d%H:%M", "%Y/%m/%d"]:
        try:
            return datetime.strptime(s, fmt)
        except:
            pass
    
    year = datetime.now().year
    month = None
    day = None
    hour = 23
    minute = 59
    
    date_match = re.search(r'(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日', s)
    if date_match:
        if date_match.group(1):
            year = int(date_match.group(1))
        month = int(date_match.group(2))
        day = int(date_match.group(3))
    
    if not month:
        date_match2 = re.search(r'(\d{1,2})[-/](\d{1,2})', s)
        if date_match2:
            month = int(date_match2.group(1))
            day = int(date_match2.group(2))
    
    time_match = re.search(r'(?:晚上|晚)?(\d{1,2})[点:](\d{1,2})?(?:分)?', s)
    if time_match:
        hour = int(time_match.group(1))
        if time_match.group(2):
            minute = int(time_match.group(2))
        if '晚上' in s or '晚' in s:
            if 1 <= hour <= 6:
                hour += 12
    
    if month and day:
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            pass
    
    digits = re.findall(r'\d+', s)
    if len(digits) >= 3:
        try:
            y, m, d = int(digits[0]), int(digits[1]), int(digits[2])
            if y < 100:
                y += 2000
            if len(digits) >= 5:
                h, mi = int(digits[3]), int(digits[4])
                return datetime(y, m, d, h, mi)
            return datetime(y, m, d, 23, 59)
        except:
            pass
    
    return datetime.now() + timedelta(days=7)

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
- 截止时间（尽量提取为 年-月-日 时:分 格式，如 2026-09-15 20:00）
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
- 截止时间（尽量提取为 年-月-日 时:分 格式）
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

# ========== 文件文本提取 ==========
def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.name.lower()
    
    try:
        if file_type.endswith('.pdf'):
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        
        elif file_type.endswith('.docx'):
            import docx
            doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        
        elif file_type.endswith('.txt'):
            return uploaded_file.getvalue().decode('utf-8').strip()
        
        else:
            return None, "不支持的文件格式，请上传 PDF、Word(.docx) 或 TXT 文件"
    
    except Exception as e:
        return None, f"文件读取失败：{str(e)}"

# ========== 保存AI提取结果 ==========
def save_extracted_data(user, data):
    ddl_str = data.get("截止时间", "")
    ddl_dt = smart_parse_time(ddl_str)
    
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

# ========== 左侧：添加/编辑任务 ==========
with st.sidebar:
    # --- 编辑模式 ---
    if st.session_state.edit_mode and st.session_state.edit_task:
        st.header("✏️ 编辑任务")
        
        task = st.session_state.edit_task
        
        try:
            old_ddl = datetime.strptime(task['截止时间'], '%Y-%m-%d %H:%M')
            old_date = old_ddl.date()
            old_time = old_ddl.time()
        except:
            old_date = datetime.now().date()
            old_time = datetime.strptime("23:59", "%H:%M").time()
        
        edit_course = st.text_input("课程名称", value=task['课程'], key="e_course")
        edit_task_name = st.text_input("任务名称", value=task['任务'], key="e_task")
        edit_date = st.date_input("截止日期", value=old_date, key="e_date")
        edit_time = st.time_input("截止时间", value=old_time, key="e_time")
        edit_submit = st.text_input("提交方式", value=task['提交方式'] if task['提交方式'] != '未填写' else '', key="e_submit")
        edit_note = st.text_area("备注", value=task['备注'] if task['备注'] != '无' else '', key="e_note")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 保存修改", type="primary", use_container_width=True):
                if edit_course and edit_task_name:
                    ddl_str = f"{edit_date} {edit_time.strftime('%H:%M')}"
                    update_task_db(task['id'], edit_course, edit_task_name, ddl_str, edit_submit, edit_note)
                    st.session_state.edit_mode = False
                    st.session_state.edit_task = None
                    st.session_state.ddl_list = load_data(current_user)
                    st.success("✅ 修改成功！")
                    st.rerun()
                else:
                    st.error("❌ 课程和任务名称不能为空")
        
        with c2:
            if st.button("❌ 取消编辑", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.edit_task = None
                st.rerun()
        
        st.divider()
    
    # --- 添加新任务 ---
    st.header("➕ 添加新任务")
    
    with st.expander("📸 AI截图识别"):
        uploaded_img = st.file_uploader(
            "上传课程通知截图",
            type=["png", "jpg", "jpeg"],
            key="img_upload"
        )
        
        if uploaded_img is not None:
            st.image(uploaded_img, caption="已上传的截图", use_container_width=True)
            
            if st.button("🔍 AI识别图片", type="primary", use_container_width=True, key="btn_img"):
                if ZHIPU_KEY == "sk-你的智谱APIKey":
                    st.error("❌ 请先修改代码中的 ZHIPU_KEY！")
                else:
                    with st.spinner("AI正在看图识字..."):
                        image_bytes = uploaded_img.getvalue()
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
    
    with st.expander("📝 粘贴文字通知"):
        notice = st.text_area("粘贴课程通知：", height=100,
            placeholder="例如：各位同学，《数据结构》第三章作业请于9月15日晚8点前提交...")
        
        if st.button("🔍 AI一键提取", use_container_width=True, key="btn_text"):
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
    
    with st.expander("📄 上传文件提取（PDF/Word/TXT）"):
        uploaded_doc = st.file_uploader(
            "上传课程文件",
            type=["pdf", "docx", "txt"],
            key="doc_upload",
            help="支持PDF、Word文档、纯文本文件"
        )
        
        if uploaded_doc is not None:
            st.write(f"已选择：**{uploaded_doc.name}**")
            
            if st.button("📖 读取并AI提取", type="primary", use_container_width=True, key="btn_doc"):
                if ZHIPU_KEY == "sk-你的智谱APIKey":
                    st.error("❌ 请先修改代码中的 ZHIPU_KEY！")
                else:
                    with st.spinner("正在读取文件内容..."):
                        result = extract_text_from_file(uploaded_doc)
                    
                    if isinstance(result, tuple) and result[0] is None:
                        st.error(result[1])
                    else:
                        text = result
                        if len(text) > 3000:
                            text = text[:3000] + "\n...（内容过长，已截取前3000字）"
                        
                        with st.expander("查看文件提取的原文"):
                            st.text(text[:500] + "..." if len(text) > 500 else text)
                        
                        with st.spinner("AI正在分析文件内容..."):
                            data, err = extract_with_ai(text)
                        
                        if err:
                            st.error(f"AI提取失败：{err}")
                        elif data:
                            save_extracted_data(current_user, data)
                            st.session_state.ddl_list = load_data(current_user)
                            st.success("✅ 文件提取成功并已保存！")
                            with st.expander("查看识别结果"):
                                st.json(data)
                            st.rerun()
    
    st.divider()
    
    with st.expander("✏️ 手动录入"):
        course = st.text_input("课程名称", placeholder="例如：数据结构", key="m_course")
        task = st.text_input("任务名称", placeholder="例如：第三章作业", key="m_task")
        ddl_date = st.date_input("截止日期", value=datetime.now() + timedelta(days=7), key="m_date")
        ddl_time = st.time_input("截止时间", value=datetime.strptime("23:59", "%H:%M").time(), key="m_time")
        submit = st.text_input("提交方式", placeholder="例如：智慧理工平台", key="m_submit")
        note = st.text_area("备注", placeholder="命名格式等...", key="m_note")
        
        if st.button("💾 手动保存", use_container_width=True, key="btn_manual"):
            if course and task:
                ddl_str = f"{ddl_date} {ddl_time.strftime('%H:%M')}"
                add_task_db(current_user, course, task, ddl_str, submit, note)
                st.session_state.ddl_list = load_data(current_user)
                st.success("✅ 添加成功！")
                st.rerun()
            else:
                st.error("❌ 课程和任务名称不能为空")
    
    st.divider()
    st.header("📊 统计")
    total = len(st.session_state.ddl_list)
    st.metric("总任务数", total)
    
    urgent = len(overdue) + len(today) + len(tomorrow)
    if urgent > 0:
        st.error(f"🔥 紧急任务：{urgent} 个")

# ========== 🔍 搜索检索 ==========
st.header("🔍 任务检索")

search_col1, search_col2 = st.columns([4, 1])

with search_col1:
    search_keyword = st.text_input(
        "输入关键词搜索（课程/任务/提交方式/备注）",
        placeholder="例如：数据结构、作业、智慧理工...",
        label_visibility="collapsed"
    )

with search_col2:
    if st.button("🔄 显示全部", use_container_width=True):
        search_keyword = ""

filtered_tasks = st.session_state.ddl_list
if search_keyword.strip():
    keyword = search_keyword.strip().lower()
    filtered_tasks = [
        item for item in st.session_state.ddl_list
        if (keyword in item['课程'].lower() or
            keyword in item['任务'].lower() or
            keyword in item['提交方式'].lower() or
            keyword in item['备注'].lower())
    ]
    st.caption(f"🔎 关键词「{search_keyword}」共找到 **{len(filtered_tasks)}** 个结果")

# ========== 主区域：任务清单 ==========
st.header(f"📋 {current_user} 的任务清单")

display_tasks = filtered_tasks if search_keyword.strip() else st.session_state.ddl_list

if not display_tasks:
    if search_keyword.strip():
        st.info(f"未找到包含「{search_keyword}」的任务，试试其他关键词")
    else:
        st.info("暂无任务，请从左侧添加（支持截图识别、文字提取、文件上传、手动录入四种方式）")
else:
    for idx, item in enumerate(display_tasks):
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
                
                if st.button("✏️ 编辑", key=f"edit_{item['id']}", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.session_state.edit_task = item
                    st.rerun()
                
                if st.button("🗑️ 删除", key=f"del_{item['id']}", use_container_width=True):
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
                ddl = datetime.strptime(item['截止时间'], '%Y-%m-%d %H:%M')
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