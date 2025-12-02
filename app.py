import streamlit as st
import pandas as pd
import itertools

# ==========================================
# 1. 核心数据与配置
# ==========================================

# 评分映射字典 (修改版)
# "我不想打" 权重已调整为 -2，与 "劣" 相同
SCORE_MAP = {
    "优": 2,
    "小优": 1,
    "均": 0,
    "平": 0,
    "小劣": -1,
    "劣": -2,
    "我不想打": -2  # 修改点：从 -100 改为 -2
}

# 颜色映射 (用于表格显示)
COLOR_MAP = {
    "优": "background-color: #d4edda; color: #155724",     # 绿色
    "小优": "background-color: #e2e6ea; color: #155724",    # 浅绿/灰绿
    "均": "background-color: #cce5ff; color: #004085",      # 蓝色
    "平": "background-color: #cce5ff; color: #004085",      # 蓝色
    "小劣": "background-color: #fff3cd; color: #856404",    # 黄/浅红
    "劣": "background-color: #f8d7da; color: #721c24",      # 红色
    "我不想打": "background-color: #343a40; color: #ffffff" # 黑色
}

# 原始数据
RAW_DATA = {
  "team_data": [
    { "player": "三毛九鬼龙", "deck": "鬼龙", "matchups": { "比雕恶喷": "优", "尾狸恶喷": "优", "沙奈朵": "劣", "鬼龙": "均", "轰鬼": "均", "密勒顿": "优", "勾喷": "劣", "LTB": "均", "纯恶月": "平", "水恶月": "小劣", "汇流梦幻": "劣", "双无梦幻": "我不想打", "水熊": "小劣", "铁武者": "优", "古剑豹": "优", "赛富豪": "优", "其它": "优" } },
    { "player": "土豆", "deck": "鬼龙", "matchups": { "比雕恶喷": "优", "尾狸恶喷": "小优", "沙奈朵": "小劣", "鬼龙": "小优", "轰鬼": "小优", "密勒顿": "小优", "勾喷": "小劣", "LTB": "均", "纯恶月": "平", "水恶月": "平", "汇流梦幻": "小优", "双无梦幻": "平", "水熊": "平", "铁武者": "优", "古剑豹": "小优", "赛富豪": "优", "其它": "优" } },
    { "player": "语申", "deck": "尾狸恶喷", "matchups": { "比雕恶喷": "平", "尾狸恶喷": "平", "沙奈朵": "劣", "鬼龙": "小劣", "轰鬼": "小劣", "密勒顿": "优", "勾喷": "小劣", "LTB": "劣", "纯恶月": "优", "水恶月": "优", "汇流梦幻": "优", "双无梦幻": "优", "水熊": "劣", "铁武者": "平", "古剑豹": "平", "赛富豪": "平", "其它": "优" } },
    { "player": "ZZ", "deck": "沙奈朵", "matchups": { "比雕恶喷": "优", "尾狸恶喷": "优", "沙奈朵": "平", "鬼龙": "优", "轰鬼": "优", "密勒顿": "平", "勾喷": "优", "LTB": "优", "纯恶月": "优", "水恶月": "优", "汇流梦幻": "优", "双无梦幻": "优", "水熊": "我不想打", "铁武者": "我不想打", "古剑豹": "优", "赛富豪": "优", "其它": "优" } },
    { "player": "乐子人", "deck": "lostK喷", "matchups": { "比雕恶喷": "优", "尾狸恶喷": "优", "沙奈朵": "劣", "鬼龙": "优", "轰鬼": "优", "密勒顿": "平", "勾喷": "平", "LTB": "平", "纯恶月": "优", "水恶月": "优", "汇流梦幻": "我不想打", "双无梦幻": "我不想打", "水熊": "劣", "铁武者": "劣", "古剑豹": "优", "赛富豪": "优", "其它": "劣" } },
    { "player": "龟龟", "deck": "涡轮梦幻", "matchups": { "比雕恶喷": "小劣", "尾狸恶喷": "劣", "沙奈朵": "劣", "鬼龙": "平", "轰鬼": "劣", "密勒顿": "优", "勾喷": "我不想打", "LTB": "优", "纯恶月": "优", "水恶月": "优", "汇流梦幻": "小劣", "双无梦幻": "平", "水熊": "优", "铁武者": "优", "古剑豹": "优", "赛富豪": "优", "其它": "优" } }
  ]
}

# ==========================================
# 2. 辅助函数
# ==========================================

def get_score(rating_text):
    """根据文字评价获取分数"""
    return SCORE_MAP.get(rating_text, 0)

def style_dataframe(val):
    """Pandas Styler 函数，用于给表格上色"""
    return COLOR_MAP.get(val, "")

def calculate_ban_pick(team_data, selected_opponents):
    """
    核心算法逻辑 (已更新支持重复卡组)
    """
    results = {}

    # --- 1. Ban 推荐计算 ---
    # 注意：这里如果对方带了2个沙奈朵，我们会计算 Ban 掉其中任意一个沙奈朵的收益
    # 实际上，Ban 掉同名卡组中的任何一个，效果是一样的
    
    # 获取唯一的对手卡组列表，避免重复计算
    unique_opponents = list(set(selected_opponents))
    opponent_scores = {} 
    
    for opp_deck in unique_opponents:
        total_score = 0
        for member in team_data:
            rating = member['matchups'].get(opp_deck, member['matchups'].get("其它", "平"))
            total_score += get_score(rating)
        opponent_scores[opp_deck] = total_score
    
    # 分数越低，威胁越大，越建议Ban
    if opponent_scores:
        ban_target = min(opponent_scores, key=opponent_scores.get)
        ban_reason_score = opponent_scores[ban_target]
    else:
        ban_target = None
        ban_reason_score = 0

    results['ban_target'] = ban_target
    results['ban_score'] = ban_reason_score
    results['opponent_scores'] = opponent_scores

    # --- 2. Pick 推荐计算 ---
    # 关键逻辑修改：如果 ban_target 是沙奈朵，且对手有2个沙奈朵，列表中只应该移除 1 个沙奈朵
    remaining_opponents = selected_opponents.copy()
    if ban_target in remaining_opponents:
        remaining_opponents.remove(ban_target) # 只移除第一个匹配项

    if not remaining_opponents:
        results['pick_combo'] = []
        results['pick_score'] = 0
        return results

    # 生成所有可能的3人组合
    all_members = [m['player'] for m in team_data]
    combos = list(itertools.combinations(all_members, 3))
    
    best_combo = None
    best_score = -float('inf')

    for combo in combos:
        current_combo_score = 0
        for player_name in combo:
            player_data = next(p for p in team_data if p['player'] == player_name)
            for opp_deck in remaining_opponents:
                rating = player_data['matchups'].get(opp_deck, player_data['matchups'].get("其它", "平"))
                current_combo_score += get_score(rating)
        
        if current_combo_score > best_score:
            best_score = current_combo_score
            best_combo = combo

    results['pick_combo'] = best_combo
    results['pick_score'] = best_score
    results['remaining_opponents'] = remaining_opponents
    
    return results

# ==========================================
# 3. Streamlit UI 界面
# ==========================================

st.set_page_config(page_title="PTCG 战队 BP 助手", page_icon="🃏", layout="wide")

st.title("🏆 PTCG 3v3 战队赛 BP 助手")

# 提取所有可能的对手卡组名称
all_possible_opponents = set()
for member in RAW_DATA['team_data']:
    all_possible_opponents.update(member['matchups'].keys())
sorted_opponents = sorted([x for x in all_possible_opponents if x != "其它"])
if "其它" in all_possible_opponents:
    sorted_opponents.append("其它")

# --- 左侧边栏 (修改版：改为独立下拉框以支持重复) ---
with st.sidebar:
    st.header("⚙️ 对局设置")
    st.info("在这里逐个选择对手卡组，支持选择重复卡组。")
    
    selected_opponents = []
    
    # 动态创建 6 个选择框
    # 为了方便演示，前4个设置默认值
    default_values = ["沙奈朵", "鬼龙", "密勒顿", "赛富豪", "(无)", "(无)"]
    
    for i in range(6):
        # 选项增加一个 "(无)"
        options = ["(无)"] + sorted_opponents
        # 设置默认值索引
        def_index = options.index(default_values[i]) if default_values[i] in options else 0
        
        deck = st.selectbox(f"对手卡组 #{i+1}", options=options, index=def_index, key=f"deck_select_{i}")
        if deck != "(无)":
            selected_opponents.append(deck)

    st.markdown("---")
    st.write(f"当前已选: {len(selected_opponents)} 套")

# --- 主界面 ---

if not selected_opponents:
    st.warning("👈 请在左侧选择对手的卡组以开始分析。")
else:
    # 1. 构建优劣势表格
    st.subheader("📊 优劣势速览表")
    
    table_data = []
    for member in RAW_DATA['team_data']:
        row = {"队员": f"{member['player']} ({member['deck']})"}
        # 表格列展示 logic：如果选了两个沙奈朵，表格显示两列沙奈朵
        for idx, opp in enumerate(selected_opponents):
            col_name = f"{opp} (#{idx+1})" # 加上编号防止表格列名重复报错
            rating = member['matchups'].get(opp, member['matchups'].get("其它", "平"))
            row[col_name] = rating
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    df.set_index("队员", inplace=True)

    # 应用样式
    st.dataframe(
        df.style.map(style_dataframe),
        use_container_width=True
    )

    st.markdown("---")

    # 2. 算法计算
    st.subheader("🧠 AI 战术建议")
    
    analysis = calculate_ban_pick(RAW_DATA['team_data'], selected_opponents)
    
    col1, col2 = st.columns(2)

    # --- Ban 建议展示 ---
    with col1:
        st.markdown("### 🔴 建议 Ban")
        ban_target = analysis['ban_target']
        if ban_target:
            st.error(f"**{ban_target}**")
            
            score = analysis['ban_score']
            st.write(f"威胁评分: {score}")
            st.write(f"理由：如果不 Ban {ban_target}，我方整体处于最大劣势。")
            if score <= -10:
                st.caption("注：即使调整了权重，这套牌依然非常难打。")
        else:
            st.info("数据不足。")

    # --- Pick 建议展示 ---
    with col2:
        st.markdown("### 🟢 建议 Pick (出战阵容)")
        pick_combo = analysis['pick_combo']
        
        if pick_combo:
            combo_str = " + ".join(pick_combo)
            st.success(f"**{combo_str}**")
            
            st.write("理由：")
            # 格式化剩余对手显示
            rem_opps = analysis['remaining_opponents']
            rem_opps_str = ", ".join(rem_opps) if rem_opps else "无"
            
            st.write(f"在 Ban 掉 {analysis['ban_target']} 后，剩余对手为：")
            st.code(rem_opps_str)
            st.write("这三位选手的综合胜算最高。")
        else:
            st.info("请先选择对手卡组。")


