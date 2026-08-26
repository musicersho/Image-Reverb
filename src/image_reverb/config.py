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

# ------------------------------------------------------------
# T-11 幾何估計（metric depth → 房間尺寸）
#
# 用 metric depth 模型（輸出單位是公尺），不是相對深度：
# T-05 實測已否定相對深度路線（同一張圖各自正規化的 disparity 與實際空間大小
# 沒有單調關係，車內 91.5x vs 體育館 11.7x）。**禁止退回相對深度模型。**
# ------------------------------------------------------------
METRIC_DEPTH_MODEL_ID = "depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf"

# 相機水平視角（度）。EXIF 讀得到焦距就換算，讀不到才用這個預設值。
DEFAULT_HFOV_DEG = 60.0

# 深度防呆（沿用 T-05 REPORT §7.3）：窗外/天空/消失點會給出荒謬的遠距離，
# 直接參與統計會把房間尺寸整個拉爆，所以先 clamp 再取 robust 統計。
DEPTH_CLAMP_MIN_M = 0.3   # 比這更近的視為雜訊（鏡頭前的手指等）
DEPTH_CLAMP_MAX_M = 50.0  # 比這更遠的視為「室內量不到」（窗外/天空/走廊消失點）
DEPTH_PERCENTILES = (5, 50, 95)  # robust 統計用的百分位

# 尺度校驗（不是主路線，只用來標低信心）：門高約 2.0m
DOOR_HEIGHT_M = 2.0
SCALE_CHECK_WARN_RATIO = 0.5  # metric 深度與門高反推的尺度偏差超過 ±50% 就標 confidence: low

# 評測關卡（T-11 卡的通過條件）：一般室內誤差門檻。
# ⚠️ 這個數字是 T-08 決策定的驗收判準，**不准為了讓測試通過而放寬**。
GEOMETRY_ERROR_TOLERANCE = 0.30  # ±30%

# 房間高度的合理範圍（metric 深度估不到天花板時的 fallback 上下限）
ROOM_HEIGHT_MIN_M = 2.0
ROOM_HEIGHT_MAX_M = 20.0

# 自動幾何（metric depth）的適用範圍上限（T-11 決策補丁，Fable 2026-08-25 定案）。
#
# 10m 這個數字的理由（不是拍腦袋）：模型實證天花板 ~20m（9 張照片最大預測距離
# 落在 3.6–19.7m），且量程壓縮在天花板之前就開始（走廊實際 30m 被壓成 12.8m）
# ——估值一旦超過這個門檻，就無法區分「真的 10–20m」與「被壓縮的 30m+」，
# 這個區間的數字不可信。另外 ±30% 判準（GEOMETRY_ERROR_TOLERANCE）目前只在 3m
# 級空間有 ground truth 驗證過（浴室 +24%）。10m = 天花板的一半，保守取值。
#
# 範圍外不是失敗，是正式行為分支：confidence 降為 low ＋警示，出口是
# --override-dims（F-09）或改用 360° 環景輸入。詳見 TASKS.md T-11 卡「Fable 路線決策」。
GEOMETRY_SCOPE_MAX_M = 10.0

GEOMETRY_OUTPUT_DIR = PROJECT_ROOT / "output" / "geometry"

# ------------------------------------------------------------
# T-12 材質模組
# ------------------------------------------------------------
MATERIALS_PATH = PROJECT_ROOT / "data" / "materials.json"

# 未指定的面用這個材質，**不是**複製地板材質（真實房間的牆不會跟地板同材質）
DEFAULT_WALL_MATERIAL = "gypsum_board"

# 二階材質分類：ADE20K 只給幾何角色，材質標籤交給 CLIP zero-shot
# （T-06 實證：滿鋪地毯只有 29.6% 被判成 rug、70.4% 判成 floor，
#   所以 floor/wall 的類別語意不採信）
SEGMENTATION_MODEL_ID = "nvidia/segformer-b4-finetuned-ade-512-512"
CLIP_MODEL_ID = "openai/clip-vit-base-patch32"

# 信心 gating：top-1 機率低於此值就 fallback generic_wall 並記 warnings
CLIP_CONFIDENCE_THRESHOLD = 0.4

# 表面區域太小就不送去分類（像素佔比），避免拿一小撮雜點決定整面牆的材質
MIN_SURFACE_AREA_RATIO = 0.01

SURFACES_OUTPUT_DIR = PROJECT_ROOT / "output" / "surfaces"

# ------------------------------------------------------------
# T-13 聲學參數計算
# ------------------------------------------------------------
# 空氣溫濕度假設（20°C/50%RH，與 T-01 `gen_ir_manual.py` 的模擬設定一致）：
# 用來查 pyroomacoustics 內建的空氣吸收表（Sabine 4mV 修正項）與換算音速。
AIR_TEMPERATURE_C = 20.0
AIR_HUMIDITY_PCT = 50.0

# pre-delay 假設：沒有真正的聲源/麥克風位置資訊，用房間尺寸的固定比例
# （進深, 寬度, 高度）推算，避免退化成同一點或貼牆角的直達距離。
PREDELAY_SOURCE_POS_FRAC = (0.25, 0.33, 0.6)
PREDELAY_MIC_POS_FRAC = (0.75, 0.67, 0.5)

ACOUSTICS_OUTPUT_DIR = PROJECT_ROOT / "output" / "acoustics"
