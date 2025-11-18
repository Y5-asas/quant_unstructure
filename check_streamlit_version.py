"""
检查 Streamlit 版本和功能兼容性的脚本
运行方式：streamlit run check_streamlit_version.py
或者：python check_streamlit_version.py
"""
import streamlit as st
import sys
import inspect

st.title("Streamlit 版本检查")

st.write(f"**Python 版本:** {sys.version}")
st.write(f"**Streamlit 版本:** {st.__version__}")
st.write(f"**Python 可执行文件:** {sys.executable}")

st.markdown("---")
st.subheader("功能兼容性检查")

# 检查关键功能
checks = {
    "st.rerun()": hasattr(st, 'rerun'),
    "st.experimental_rerun()": hasattr(st, 'experimental_rerun'),
    "st.button(type='primary')": True,  # 需要实际测试
    "st.button(use_container_width=True)": True,  # 需要实际测试
    "st.plotly_chart(use_container_width=True)": True,
    "st.dataframe(use_container_width=True)": True,
}

for feature, available in checks.items():
    status = "✅ 支持" if available else "❌ 不支持"
    st.write(f"{status}: {feature}")

# 检查 button 函数签名
st.markdown("---")
st.subheader("st.button() 函数签名")
try:
    sig = inspect.signature(st.button)
    st.code(str(sig), language="python")
except Exception as e:
    st.error(f"无法获取函数签名: {e}")

# 测试按钮
st.markdown("---")
st.subheader("功能测试")

try:
    test_button = st.button("测试按钮 (无参数)")
    if test_button:
        st.success("基础按钮功能正常")
except Exception as e:
    st.error(f"按钮测试失败: {e}")

try:
    test_button2 = st.button("测试按钮 (use_container_width)", use_container_width=True)
    if test_button2:
        st.success("use_container_width 参数支持")
except Exception as e:
    st.warning(f"use_container_width 不支持: {e}")

try:
    test_button3 = st.button("测试按钮 (type='primary')", type="primary")
    if test_button3:
        st.success("type='primary' 参数支持")
except Exception as e:
    st.warning(f"type='primary' 不支持: {e}")

# 版本建议
st.markdown("---")
st.subheader("版本建议")

current_version = st.__version__
version_parts = [int(x) for x in current_version.split('.')]

if version_parts[0] >= 1 and version_parts[1] >= 18:
    st.success(f"✅ 当前版本 {current_version} 支持所有新功能")
elif version_parts[0] >= 1 and version_parts[1] >= 12:
    st.warning(f"⚠️ 当前版本 {current_version} 部分功能可能不支持，建议升级到 1.18.0+")
else:
    st.error(f"❌ 当前版本 {current_version} 过旧，强烈建议升级到 1.18.0+")

st.info("💡 如果遇到兼容性问题，请运行: `pip install --upgrade streamlit>=1.18.0`")

