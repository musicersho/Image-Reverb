# BASELINE.stable.md — T-46 criteria v3 基線 B0 穩定投影（程式產生，勿手改；§5.2 硬比對物件）

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

- B0 commit（worktree git rev-parse HEAD）：23f2abada92aa9d46b1da0ac1ba2a7f1dc178872

| 照片 | photo sha256 | analysis_stable_sha256 |
|---|---|---|
| CathedralRoom | d4dcaed7c3b590546aa26e006930b1dfc1050e509cca20e4d806a050773c9d48 | 5c4c857e21297d4b8984c1d7541d490fb1b90a9211d0362e6f6bdddce6aea47d |
| DivorceBeach | 746d0c7adfe71a30805ae41366d48e2195e42cd8f6094b79a2623fcd0c63928a | 8d4654b2bb9d7fd7dbb1f580530ebfe8a15cdce80eaa50753fd0145a75ee9711 |
| RacquetballCourt4 | 878ee129bf633cb4d4e6589d04743fd7ceae7325d2e9eee2d1e753f678a835d2 | 781debd4b08323173ab30f6c5f3f5563d595bcf29b976ab2c780c07d8a59ba7a |
| SteinmanHall | 1d2e11433e4285c0453ffed64c916307c5b97b8e5ca35826650a263baa5d0696 | 5c827c349f7dd52e28fe9c74b2567f2a87c50d436e8e5d0c74a2f5239b666a04 |
| TunnelToHell | 51dde5694fca64df43ac466da52bbcb926cd048641d79c67763cbbfc42045e65 | edc78dfafe79814309f575f4a0a401ad9efb2c9d9ec42722fbebd87d643d3b52 |
| arena_ntsu_linkou | 2b72af99bbaf6ae791b4c462af1da4808a4fded5f4cb39f9a3f1eb89df0a9b10 | 0319b79c7e60f0088862d1679e983241058c43bb245ea8088821f2c8831e9e4e |
| bathroom_tiled | 1f7ced1531d50ff9ed839315ad85063d6bfc6a699cbd63467481b56a44e35d73 | 26fd2406549b1b8a86d3a819d541d3b4646c9ac2160d77a9edf98deb9bffaea7 |
| bedroom_ai_generated | b108578269b96adcdcabac65641c766ff1a7e3e5243707a2ce5014858434bde5 | 52b84830b08977a13fecbe841687422c27b913e34d0df3d40b1743f2594b399c |
| car_interior_suv | 7dd1c6b2a154fea934e0ecc4790d18de46276be52f291d6a6eb873cf06ca0cc5 | 7dd7a098955c10cf386e6c7fe874993c1ff3d8b927a3badaa62c1be039232f08 |
| site_photo_department_store | a3aa38e1821829ce12e0f2a25294db35a32cf297172cc0a8376e34cf9c568a5c | aa60b379641c56bcc65e725a2174e3961ad2ac2d44f9e14d41dc7a48979d0a40 |
| site_photo_gym | 9ccc9c335ff8862a7f46f22548c1d1c90e9b4b79090cfaf9dd25f2346a96749e | 3939e9bd085c34f97a1069a2ed699fea40b66e978c532012c412f3c29994a350 |
| site_photo_restaurant | a3576a3a2eb8993ca87b6c8df864f5e0b7421316a91880176d59c6f340d27214 | 97943d1d1c8e0f5c5dd5eca5f0d419c8179473b21940b4398d51c5f685e41bf5 |
| stairwell_tiled | 40859d6e815202a700b237625e33e177ec6f3193cd5e409231ef0c0385b370fa | 0cb58f845d8ba62960fc05c59be9b0556bec166db3c857184d75dc74deff1d4a |
