"""T-10：管線參數集中設定。

想調整前處理行為（黑邊裁切靈敏度、環景判定門檻、投影視角）就改這裡，
不要把數字散落在 preprocess.py 裡。
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "preprocess"

# ------------------------------------------------------------
# 黑邊 / letterbox 偵測（地雷第 4 條：YouTube 截圖黑邊會毀掉深度正規化）
#
# 判定邏輯：從四個邊緣往內掃描每一列/欄，用 p90-p10（去除離群值後的亮度
# 分佈範圍）判斷是否為「純色邊框」——純色邊框的 p90-p10 會非常接近 0，
# 即使邊框不是純黑（例如字幕條的白邊）也抓得到；反之，畫面偏暗但有紋理的
# 正常內容（例如洞穴照片邊緣）p90-p10 會明顯偏高，不會被誤裁。
# ------------------------------------------------------------
BORDER_SPREAD_THRESHOLD = 3.0  # p90-p10 小於此值（0-255 尺度）視為純色邊框
BORDER_MAX_CROP_RATIO = 0.45  # 單邊最多裁掉整體寬/高的比例，避免暗色照片被裁光

# ------------------------------------------------------------
# 環景（equirectangular）偵測 —— 只看長寬比，不看檔名
# ------------------------------------------------------------
EQUIRECT_ASPECT_RATIO = 2.0
EQUIRECT_ASPECT_TOLERANCE = 0.05  # 容差 ±5%

# ------------------------------------------------------------
# equirect → 多視角透視投影
# 水平 4 視角（方位角 0/90/180/270°）＋ 仰角 ±45° 上下各 1，共 6 視角
# ------------------------------------------------------------
PERSPECTIVE_FOV_DEG = 90.0
PERSPECTIVE_OUT_SIZE = (768, 768)  # 輸出透視圖 (寬, 高)

PERSPECTIVE_VIEWS = [
    {"name": "az000_el00", "azimuth_deg": 0, "elevation_deg": 0},
    {"name": "az090_el00", "azimuth_deg": 90, "elevation_deg": 0},
    {"name": "az180_el00", "azimuth_deg": 180, "elevation_deg": 0},
    {"name": "az270_el00", "azimuth_deg": 270, "elevation_deg": 0},
    {"name": "el+45", "azimuth_deg": 0, "elevation_deg": 45},
    {"name": "el-45", "azimuth_deg": 0, "elevation_deg": -45},
]
