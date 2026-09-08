# BASELINE.md — T-46 criteria v2 基線 B0（程式產生，勿手改）

B0 定義（criteria v2 §2.1）：commit `23f2aba`（role_aware 尚未預設啟用的最後狀態；是 T-44 系列中間 commit，不是 T-44 之前）的真實 CLI 實跑結果。

## 表：13 張照片的 B0 結果

| 照片 | geometry_confidence | materials_confidence | overall confidence | gate | surfaces | surfaces_sources |
|---|---|---|---|---|---|---|
| bathroom_tiled | medium | low | low | BLOCK | {"west": "generic_wall", "east": "generic_wall", "south": "generic_wall", "north": "generic_wall", "floor": "gypsum_board", "ceiling": "gypsum_board"} | {"floor": "fallback", "west": "clip", "east": "clip", "south": "clip", "north": "clip"} |
| bedroom_ai_generated | medium | low | low | BLOCK | {"west": "generic_wall", "east": "generic_wall", "south": "generic_wall", "north": "generic_wall", "floor": "gypsum_board", "ceiling": "gypsum_board"} | {"floor": "fallback", "west": "clip", "east": "clip", "south": "clip", "north": "clip"} |
| stairwell_tiled | medium | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "gypsum_board", "ceiling": "gypsum_board"} | {"floor": "fallback", "ceiling": "fallback", "west": "fallback", "east": "fallback", "south": "fallback", "north": "fallback"} |
| arena_ntsu_linkou | low | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "gypsum_board", "ceiling": "audience_seating"} | {"ceiling": "clip", "west": "fallback", "east": "fallback", "south": "fallback", "north": "fallback"} |
| car_interior_suv | low | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "curtain_fabric", "ceiling": "gypsum_board"} | {"floor": "clip", "west": "out_of_domain", "east": "out_of_domain", "south": "out_of_domain", "north": "out_of_domain"} |
| CathedralRoom | medium | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "gypsum_board", "ceiling": "gypsum_board"} | {"north": "fallback", "east": "fallback", "south": "out_of_domain", "west": "fallback", "ceiling": "out_of_domain", "floor": "fallback"} |
| DivorceBeach | low | medium | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "concrete", "ceiling": "gypsum_board"} | {"floor": "clip"} |
| site_photo_department_store | medium | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "acoustic_panel", "ceiling": "gypsum_board"} | {"floor": "clip", "ceiling": "fallback", "west": "fallback", "east": "fallback", "south": "fallback", "north": "fallback"} |
| site_photo_gym | low | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "acoustic_panel", "ceiling": "gypsum_board"} | {"floor": "clip", "west": "out_of_domain", "east": "out_of_domain", "south": "out_of_domain", "north": "out_of_domain"} |
| site_photo_restaurant | low | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "gypsum_board", "ceiling": "curtain_fabric"} | {"ceiling": "clip", "west": "fallback", "east": "fallback", "south": "fallback", "north": "fallback"} |
| RacquetballCourt4 | medium | low | low | BLOCK | {"west": "curtain_fabric", "east": "gypsum_board", "south": "glass", "north": "gypsum_board", "floor": "wood_panel", "ceiling": "gypsum_board"} | {"north": "fallback", "east": "clip", "south": "clip", "west": "clip", "ceiling": "out_of_domain", "floor": "clip"} |
| SteinmanHall | low | low | low | BLOCK | {"west": "curtain_fabric", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "gypsum_board", "ceiling": "curtain_fabric"} | {"north": "fallback", "east": "fallback", "south": "fallback", "west": "clip", "ceiling": "clip", "floor": "fallback"} |
| TunnelToHell | low | low | low | BLOCK | {"west": "gypsum_board", "east": "gypsum_board", "south": "gypsum_board", "north": "gypsum_board", "floor": "gypsum_board", "ceiling": "gypsum_board"} | {"floor": "out_of_domain", "ceiling": "fallback", "west": "fallback", "east": "fallback", "south": "fallback", "north": "fallback"} |

## Manifest

- worktree `git rev-parse HEAD`：`23f2abada92aa9d46b1da0ac1ba2a7f1dc178872`（須等於 `23f2aba` 全長雜湊，本檔產生時已驗證相符）
- 產生時主 repo 的 `git rev-parse HEAD`：`c8f6be9b60fbb7030a27687436c4dd5fbe97c495`
- 產生時間（UTC）：2026-09-08T06:07:27.724781+00:00

| 照片 | photo sha256 | analysis.json sha256 |
|---|---|---|
| CathedralRoom | d4dcaed7c3b590546aa26e006930b1dfc1050e509cca20e4d806a050773c9d48 | 1cfbc1f697eedaec86b37634ec0bd07f216c6af8abeb839722f3ed67b1c769b7 |
| DivorceBeach | 746d0c7adfe71a30805ae41366d48e2195e42cd8f6094b79a2623fcd0c63928a | 0fd3fd12541b01e23fd46e84ad4b09940fb12d0956e546b9ac1af94acd5812dd |
| RacquetballCourt4 | 878ee129bf633cb4d4e6589d04743fd7ceae7325d2e9eee2d1e753f678a835d2 | f8c17434557cb483840e6f6f39a844db99a98537e982104a9f127632559e389a |
| SteinmanHall | 1d2e11433e4285c0453ffed64c916307c5b97b8e5ca35826650a263baa5d0696 | f7209e74b0335f8f383e5749956977f18ffd44ef20cc75e90d8e1b10ea38bab1 |
| TunnelToHell | 51dde5694fca64df43ac466da52bbcb926cd048641d79c67763cbbfc42045e65 | 75deb10201ec1f6d4a5c05c13d52a4bd5473bdd990a4c923be32a38ab7445def |
| arena_ntsu_linkou | 2b72af99bbaf6ae791b4c462af1da4808a4fded5f4cb39f9a3f1eb89df0a9b10 | ce67ef2b368d0914266c92036ab7bacd9102bcbbdf6f070d6d19eb687dd9c37e |
| bathroom_tiled | 1f7ced1531d50ff9ed839315ad85063d6bfc6a699cbd63467481b56a44e35d73 | 3e6ad9358c5b97c6a861fa25cfa05152545a8d51a5f9890e2879d3b8274aa5c3 |
| bedroom_ai_generated | b108578269b96adcdcabac65641c766ff1a7e3e5243707a2ce5014858434bde5 | 13500d0bb5403f2983cd3d605e5b09a3d25cb14ef0894fda196e25e6c0bc4775 |
| car_interior_suv | 7dd1c6b2a154fea934e0ecc4790d18de46276be52f291d6a6eb873cf06ca0cc5 | 0b5535f07a85d8a538dc5e5215b3494a8708d61fbc3b488e8f411f27973386c8 |
| site_photo_department_store | a3aa38e1821829ce12e0f2a25294db35a32cf297172cc0a8376e34cf9c568a5c | 262f8badca4e97df1151caf729a5a7de2f5aed533152e6450507578ca85ec5bc |
| site_photo_gym | 9ccc9c335ff8862a7f46f22548c1d1c90e9b4b79090cfaf9dd25f2346a96749e | 17f86c9cb7a5e920b8ecf1fb0f49ad7b790a30760d10a0503c2178cbc4472773 |
| site_photo_restaurant | a3576a3a2eb8993ca87b6c8df864f5e0b7421316a91880176d59c6f340d27214 | 9b06229bb2dbb4dd3e33e38cfcbd86a07dcce2e3aefbdcc3cdeede059bf91c89 |
| stairwell_tiled | 40859d6e815202a700b237625e33e177ec6f3193cd5e409231ef0c0385b370fa | 7a21f80c300ef371485728f1fe593c3e8b35c65a1431ad65e270a5ba31287fa3 |
