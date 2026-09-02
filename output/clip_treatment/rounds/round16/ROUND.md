# Round `round16` — T-44 role-aware 分區輪紀錄

- status: complete
- 父輪次: round15_role_partition
- 執行指令: `python scripts/t44_role_eval.py round16 --hypothesis PLAN_T44.md §7：floor 加回 generic_wall（稀釋 bathroom_tiled.floor 的 carpet 搶答）；wall 整組還原全域 12 種候選（round15 wall 零修正三倒退，acoustic_panel/curtain_fabric 依完整性鐵則不能排除，找不到合法正面槓桿）；ceiling 不動 --parent round15_role_partition --role-sensitivity`
- 本輪假設與修改理由: PLAN_T44.md §7：floor 加回 generic_wall（稀釋 bathroom_tiled.floor 的 carpet 搶答）；wall 整組還原全域 12 種候選（round15 wall 零修正三倒退，acoustic_panel/curtain_fabric 依完整性鐵則不能排除，找不到合法正面槓桿）；ceiling 不動

## ROLE_MATERIAL_CANDIDATES 分區表快照

```json
{
  "floor": [
    "concrete",
    "carpet",
    "wood_panel",
    "gypsum_board",
    "marble",
    "audience_seating",
    "generic_wall"
  ],
  "ceiling": [
    "concrete",
    "curtain_fabric",
    "generic_wall",
    "gypsum_board"
  ],
  "wall": [
    "concrete",
    "brick",
    "wood_panel",
    "gypsum_board",
    "glass",
    "marble",
    "carpet",
    "curtain_fabric",
    "acoustic_panel",
    "audience_seating",
    "grass_soil",
    "generic_wall"
  ]
}
```

## 相對 round15_role_partition（本卡首輪）的分區表差異

- floor：新增 ['generic_wall']
- wall：新增 ['audience_seating', 'carpet', 'wood_panel']

## CLIP_MATERIAL_PROMPTS 字串（本卡不動，附快照供核對）

```json
{
  "CLIP_MATERIAL_PROMPTS": {
    "concrete": "a smooth poured concrete surface",
    "brick": "a bare unglazed brick surface",
    "wood_panel": "a wooden panel or wood plank surface",
    "gypsum_board": "a painted plasterboard drywall surface",
    "glass": "a pane of clear glass or a window",
    "marble": "a polished marble or ceramic tile surface",
    "carpet": "a thick carpet or textile floor covering",
    "curtain_fabric": "a heavy fabric curtain or drape",
    "acoustic_panel": "a fibrous acoustic absorption panel",
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

## 正確率數字

| 指標 | 數值 |
|---|---|
| overall | 31/76 |
| floor | 4/13 |
| ceiling | 4/11 |
| wall | 23/52 |
| in-set 誤判 | 9 |
| 非 proxy 正確率 | 30/63 |
| proxy 正確率 | 1/13 |

## 對照比較基線 round11_remap_baseline（overall 30/76、floor 4/13、ceiling 3/11、wall 23/52、非 proxy 30/63、in-set 誤判 9）

overall 31/76 （上升 相對 30）；floor 4/13 （持平 相對 4）；in-set 誤判 9 （持平 相對 9）。

## 按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 23 | 1 | 13/22（59.1%） |
| fallback | 29 | 0 | 13/29（44.8%） |
| out_of_domain | 15 | 0 | 5/15（33.3%） |
| 無來源 | 11 | 1 | 0/10（0.0%） |

## 指紋（沿用 `eval_cache.py` 六類指紋）

| 項目 | 值 |
|---|---|
| code_sha256 | {"preprocess.py": "f3d1d2f820087f603ff5cde90c6a4905ec87513fd3d846440c2f79ee7f6b8352", "surfaces.py": "d07f153ba5a6cb26a5ee61d16ac8f6b67a38f35a63b14eeff391fcdcb49dbe37", "config.py": "c1e09da90283cb20b3a1c672f0b3150c6f6c280d6d83adeeb218b6413fc176c4"} |
| data_sha256 | {"materials.json": "dddf5bd0a3680419e594a17de44e28269c64b038f7100cb7cf5faedf0acb1c3a", "material_ground_truth.json": "965e51ac19e2d25a61b89bb8b94c01e4f34e3e41d6300002627d212abfc430c7"} |
| segmentation_model_id | nvidia/segformer-b4-finetuned-ade-512-512 |
| clip_model_id | openai/clip-vit-base-patch32 |
| clip_threshold | 0.4 |
| eval_mode | t44_role_aware:round16 |

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
