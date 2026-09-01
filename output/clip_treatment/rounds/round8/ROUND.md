# Round `round8` — T-38 治療輪紀錄

- status: complete
- 父輪次: round7
- 執行指令: `python scripts/t38_treatment_eval.py round8 --hypothesis 改 acoustic_panel 提示詞（PLAN.md round8，累積 round7 的 concrete 改動）：鎖定 acoustic_panel→carpet 2 面誤判（department_store／gym floor），假設現有字串只講纖維質感、沒有排除軟質地面覆蓋物，改法加入安裝在牆面／天花板上的硬質板材描述 --parent round7`
- 本輪假設與修改理由: 改 acoustic_panel 提示詞（PLAN.md round8，累積 round7 的 concrete 改動）：鎖定 acoustic_panel→carpet 2 面誤判（department_store／gym floor），假設現有字串只講纖維質感、沒有排除軟質地面覆蓋物，改法加入安裝在牆面／天花板上的硬質板材描述

## CLIP_MATERIAL_PROMPTS / CLIP_OOD_PROMPTS 快照

```json
{
  "CLIP_MATERIAL_PROMPTS": {
    "concrete": "a poured concrete surface with a subtle grainy texture and a cool grey tone, whether bare or painted",
    "brick": "a bare unglazed brick surface",
    "wood_panel": "a wooden panel or wood plank surface",
    "gypsum_board": "a painted plasterboard drywall surface",
    "glass": "a pane of clear glass or a window",
    "marble": "a polished marble or ceramic tile surface",
    "carpet": "a thick carpet or textile floor covering",
    "curtain_fabric": "a heavy fabric curtain or drape",
    "acoustic_panel": "a rigid fibrous acoustic foam or felt panel mounted on a wall or ceiling, not a floor covering",
    "audience_seating": "rows of upholstered seats with an audience",
    "grass_soil": "natural grass or bare soil ground",
    "generic_wall": "a plain smooth plastered wall"
  },
  "CLIP_OOD_PROMPTS": {
    "__vehicle_interior": "the inside of a car or vehicle cabin",
    "__outdoor_scene": "an outdoor landscape with sky and trees",
    "__object_closeup": "a close-up photograph of a small object",
    "__person": "a photograph of a person's face or body"
  }
}
```

## 相對 round0_baseline 的字串差異

- CLIP_MATERIAL_PROMPTS.acoustic_panel：「a fibrous acoustic absorption panel」→「a rigid fibrous acoustic foam or felt panel mounted on a wall or ceiling, not a floor covering」
- CLIP_MATERIAL_PROMPTS.concrete：「a smooth poured concrete surface」→「a poured concrete surface with a subtle grainy texture and a cool grey tone, whether bare or painted」

## 正確率數字

| 指標 | 數值 |
|---|---|
| overall | 24/76 |
| floor | 3/13 |
| in-set 誤判 | 18 |
| clip 來源正確率 | 8/26 |
| 非 proxy 正確率 | 23/60 |
| proxy 正確率 | 1/16 |

## 按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 27 | 1 | 8/26（30.8%） |
| fallback | 25 | 0 | 14/25（56.0%） |
| out_of_domain | 15 | 0 | 1/15（6.7%） |
| 無來源 | 11 | 1 | 1/10（10.0%） |

## 指紋（沿用 `eval_cache.py` 六類指紋）

| 項目 | 值 |
|---|---|
| code_sha256 | {"preprocess.py": "f3d1d2f820087f603ff5cde90c6a4905ec87513fd3d846440c2f79ee7f6b8352", "surfaces.py": "633247db30f4eb41d8bd0cc2f2e9edee314f6cc1ad75ef76f67362d4d96d527c", "config.py": "c1e09da90283cb20b3a1c672f0b3150c6f6c280d6d83adeeb218b6413fc176c4"} |
| data_sha256 | {"materials.json": "8afb86e4a44cbb85fc274b1f9369aa598c816a8f1bb60a0f612e5007cd48127f", "material_ground_truth.json": "a4116632e61d90ebcb8cd985fca889762dc57a5c9ad1873b2095f03a70c8b20c"} |
| segmentation_model_id | nvidia/segformer-b4-finetuned-ade-512-512 |
| clip_model_id | openai/clip-vit-base-patch32 |
| clip_threshold | 0.4 |
| eval_mode | treatment:round8 |

### 逐張照片 photo_sha256

| 照片 | sha256 |
|---|---|
| CathedralRoom | d4dcaed7c3b590546aa26e006930b1dfc1050e509cca20e4d806a050773c9d48 |
| DivorceBeach | 746d0c7adfe71a30805ae41366d48e2195e42cd8f6094b79a2623fcd0c63928a |
| RacquetballCourt4 | 878ee129bf633cb4d4e6589d04743fd7ceae7325d2e9eee2d1e753f678a835d2 |
| SteinmanHall | 1d2e11433e4285c0453ffed64c916307c5b97b8e5ca35826650a263baa5d0696 |
| TunnelToHell | 51dde5694fca64df43ac466da52bbcb926cd048641d79c67763cbbfc42045e65 |
| arena_ntsu_linkou | 2b72af99bbaf6ae791b4c462af1da4808a4fded5f4cb39f9a3f1eb89df0a9b10 |
| bathroom_tiled | 1f7ced1531d50ff9ed839315ad85063d6bfc6a699cbd63467481b56a44e35d73 |
| bedroom_ai_generated | b108578269b96adcdcabac65641c766ff1a7e3e5243707a2ce5014858434bde5 |
| car_interior_suv | 7dd1c6b2a154fea934e0ecc4790d18de46276be52f291d6a6eb873cf06ca0cc5 |
| site_photo_department_store | a3aa38e1821829ce12e0f2a25294db35a32cf297172cc0a8376e34cf9c568a5c |
| site_photo_gym | 9ccc9c335ff8862a7f46f22548c1d1c90e9b4b79090cfaf9dd25f2346a96749e |
| site_photo_restaurant | a3576a3a2eb8993ca87b6c8df864f5e0b7421316a91880176d59c6f340d27214 |
| stairwell_tiled | 40859d6e815202a700b237625e33e177ec6f3193cd5e409231ef0c0385b370fa |

詳細逐面判定與 in-set 誤判明細見同目錄 `tables.md`。
