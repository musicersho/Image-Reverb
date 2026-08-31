# clip_accuracy 凍結基線 FREEZE_MANIFEST（T-40 產出，鐵則 4 唯一允許例外）

本檔案以外，本目錄下所有既有檔案自本檔產生起一個 bit 都不許變。
若要重新驗證，逐檔重算 sha256 並與下表比對——不符即代表凍結基線被覆寫過。

產生指令：`python scripts/t40_freeze_manifest.py`

| 相對路徑 | sha256 |
|---|---|
| REPORT.md | 1c8e61ff169235da0e26e8421de4145be250156d39b0256d8cfc9b131e11e047 |
| runs/CathedralRoom/detail.json | c00cb01d7673c2c56526df52153cfc75965359d51f55540a03e9dd22adeff3bb |
| runs/CathedralRoom/preprocess/CathedralRoom/cropped_equirect.png | 5f00e7271a998b1e2ab2033834881517f169fb5d7f149bbc5b11d25c76844636 |
| runs/CathedralRoom/preprocess/CathedralRoom/meta.json | 9cc1386ab2ca794de789f02e04bfdb52967b46f7c8537047ec64fba24327bf53 |
| runs/CathedralRoom/preprocess/CathedralRoom/view_az000_el00.png | fca4246859853029203f0766a9341de12bc1b7723f17c486ed8c0630047b2026 |
| runs/CathedralRoom/preprocess/CathedralRoom/view_az090_el00.png | 3724b5e3657fba37647194d78b9555db5d8adfae48a5d9bacc3b0175181dbd16 |
| runs/CathedralRoom/preprocess/CathedralRoom/view_az180_el00.png | a1545a103545dd9f8399626252afefdd2115c043a4974569b2b935a02874f4b9 |
| runs/CathedralRoom/preprocess/CathedralRoom/view_az270_el00.png | bffb00dbce687eca1bd5d51af0d9c8f8634dfbef67506d5ac689684a5cbe266e |
| runs/CathedralRoom/preprocess/CathedralRoom/view_el+45.png | d31cf87c4b252b56718cd762f890a92016e978e9c00a6cb63843d43bacdf6a92 |
| runs/CathedralRoom/preprocess/CathedralRoom/view_el-45.png | b470af0fea9d0a1a7fc276d3ea44ad3aebc0f9be9f1108e2629ffc8fcd5fa2f7 |
| runs/DivorceBeach/detail.json | 8d36e569559db4ed0ba17aa5ac8543d6a9c72b9fa91df27c32a1fd5de032c327 |
| runs/DivorceBeach/preprocess/DivorceBeach/cropped_equirect.png | 2f56663177a88e78728e2aaff07d710c7eadf78fa31a70cf97e6387e5443b460 |
| runs/DivorceBeach/preprocess/DivorceBeach/meta.json | 740edbb39c5350778b0c4da6ba126b387814830e414813e9beed591d35c65037 |
| runs/DivorceBeach/preprocess/DivorceBeach/view_az000_el00.png | d0fbe8968d96578d5d3e43e89b9282a249dc29db86ba3f1cb097c7975acb37da |
| runs/DivorceBeach/preprocess/DivorceBeach/view_az090_el00.png | a70eff11f3ec9931add37af3d791c225a4ab9a302838ccdfbf329451eb73e3ae |
| runs/DivorceBeach/preprocess/DivorceBeach/view_az180_el00.png | 2bdc3c7ceeb5d50c8f5ee35a9ffaf254d94d220acdd5a94be966ba09495f0f58 |
| runs/DivorceBeach/preprocess/DivorceBeach/view_az270_el00.png | 552111f95dba2cf7148b21ddbe73b49e3e4ddae323518b235ea3b6fea5141dff |
| runs/DivorceBeach/preprocess/DivorceBeach/view_el+45.png | 45aa077cf6e3a5efa86915fd34ccdf1b672c1d69474d21108bac3a3032853d18 |
| runs/DivorceBeach/preprocess/DivorceBeach/view_el-45.png | 6f4c454617e236fbcc42d3cc03f1bd9172e459c4f17f674f1a4015968c174e35 |
| runs/RacquetballCourt4/detail.json | 7cc2e8b4d275c81e0621df0348b7c2f707c7c78cb16829d86602eb07b3488858 |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/cropped_equirect.png | a82fd57e173a8d627ad5eeecc04d922f42762fa5ea93ddc93014ee08b969af43 |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/meta.json | 99e54993b2ba7b3d8b3acb8896fd0b331bf0f94abb47d17d3996aa6dbddab2a9 |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/view_az000_el00.png | b21d26a218e613fd2d69bd6a70c0a17999a5d9c6e7c88c2f562fbbf6119a0c5c |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/view_az090_el00.png | e354da2f5f4861504ed2e35f83a7dd4c4b43ffcc6f847d15bb5d3cc2bbb1e757 |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/view_az180_el00.png | 359b45030c3ea708416c894cf884dd3f483f19722e798a9ed824cf64255474b2 |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/view_az270_el00.png | 3061d715e8f1a8399d5083a7de5c4d397bbf2360e4c2f5df8c4ab05a1b7c00d2 |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/view_el+45.png | 903328c993c1d144246738242ce7d3d4bd7d9f5de94d1eb30874c52ca1e9b7b6 |
| runs/RacquetballCourt4/preprocess/RacquetballCourt4/view_el-45.png | 5c59affc2ca8b07d7f7f13ddca1831b3f15eaf50a3b81428302a65a87241c915 |
| runs/SteinmanHall/detail.json | c10e7a5b21d5a8e2cca5c37c060f34367635120e06bd1f006f0b1596b0f32494 |
| runs/SteinmanHall/preprocess/SteinmanHall/cropped_equirect.png | eaa24992824e465cb7799cc8a9ab479a35a33083aafe678f7caca0c1821dd18d |
| runs/SteinmanHall/preprocess/SteinmanHall/meta.json | 00cfe140ea497fc7cd7445b078985f13686dc001c43123c88cd50fdba951c728 |
| runs/SteinmanHall/preprocess/SteinmanHall/view_az000_el00.png | 03c9e5fba4f19512069cc9bab09f4816968ede70ff3bea078e14330c28a0e5ca |
| runs/SteinmanHall/preprocess/SteinmanHall/view_az090_el00.png | 885dfb957dee3faf4f00c4a7385eb202625e379e33cc8937dd745ce373647673 |
| runs/SteinmanHall/preprocess/SteinmanHall/view_az180_el00.png | 4039dac6e4d62c1d83cbd4a284ef338a0d9a739db9e1d1a5c403927b0f10c1a1 |
| runs/SteinmanHall/preprocess/SteinmanHall/view_az270_el00.png | ac89f19c56ef049c475fa9a401f8505cdc726053da81f686d6228b3744b73e4c |
| runs/SteinmanHall/preprocess/SteinmanHall/view_el+45.png | ea7c8e9ff2fb92cfe1b5dcd1bc150e9a543cc25a25aeb24a242d4e96e92059c8 |
| runs/SteinmanHall/preprocess/SteinmanHall/view_el-45.png | 2c1c8d0377e1a62ee7107ec97d4275eb6ddfad2c49f36922d52f0c92018f2fd3 |
| runs/TunnelToHell/detail.json | 9c238187a0fcb96ecf79b1820cfa259d5d6a03ba85fa6250d2d5cdb61533a33f |
| runs/TunnelToHell/preprocess/TunnelToHell/cropped_equirect.png | 9e22b269ed8d7625ec9dbd4e03eb2376bf075b0a103f94ea0397467822978ee2 |
| runs/TunnelToHell/preprocess/TunnelToHell/meta.json | 77c9dbf1ae6698c3ed8a6356215e8bd26de2a4a9114a0b4dc45c0fccbb7b684f |
| runs/TunnelToHell/preprocess/TunnelToHell/view_az000_el00.png | 981df4e2a35baa42bd0354b86a695934f10098a33b6a69c4d49901c720abd749 |
| runs/TunnelToHell/preprocess/TunnelToHell/view_az090_el00.png | 0d6e567c70ff742e35d8c24e5f72149a72317a0cd75396a5d89a059caf5d407e |
| runs/TunnelToHell/preprocess/TunnelToHell/view_az180_el00.png | ea76972a2427ec96949cb785baba09e79b526446c11da0e4ab29ce95ea12313b |
| runs/TunnelToHell/preprocess/TunnelToHell/view_az270_el00.png | be592d3bcb95bb7c6fc8926b0d908d0d58f6536fdf1b007fd0a07ff01c04a0b2 |
| runs/TunnelToHell/preprocess/TunnelToHell/view_el+45.png | 362dab3a94ab5f4b51a6658d37549189bc4de56971fe5160294ffbe1d2c4ac66 |
| runs/TunnelToHell/preprocess/TunnelToHell/view_el-45.png | 87d6b75eefc977bbdc724d21ef6fb5b2000bfa05fd0bf1976293ac885fb51d6a |
| runs/arena_ntsu_linkou/detail.json | a3ca845088109e46c68f8082f8a385d4fb919ef7f86d029391302a5b2785ec2f |
| runs/arena_ntsu_linkou/preprocess/arena_ntsu_linkou/cropped.png | 504ae1b8a532a8578a1b3e151a7c7f97c6ed7c59ccaa5264e2f183c6ce2b4e64 |
| runs/arena_ntsu_linkou/preprocess/arena_ntsu_linkou/meta.json | 697f1f8f33d5d6cae3e3f9af04dbed748a82e5a252586fb5d6486df734963259 |
| runs/bathroom_tiled/detail.json | ce4a97fce49a9aff7aa78473edf7349a9b5348d60ed67cae708192cca1d52884 |
| runs/bathroom_tiled/preprocess/bathroom_tiled/cropped.png | ca47caf11400ed4ca91d077cc14a2ca9038573d3201b6d4ecd22001ba886c582 |
| runs/bathroom_tiled/preprocess/bathroom_tiled/meta.json | bd363f12c04c2516cea9629dd513bdba924d7c47740e33f2eb75bd5f1ee3c14b |
| runs/bedroom_ai_generated/detail.json | 2a2602fae667300ddc9415426e4b70473d98c36e17b216738be5746760293df2 |
| runs/bedroom_ai_generated/preprocess/bedroom_ai_generated/cropped.png | 627f713c5a40c957da516ef04ca95b0e6f9121d64fc0d39dcbf7c5223d050f72 |
| runs/bedroom_ai_generated/preprocess/bedroom_ai_generated/meta.json | a9ab717ed4777751b88ea1f90453eb19b321991da729871ef484175801293991 |
| runs/car_interior_suv/detail.json | 97206fa044e4dbf0cccf80e85d278ec633bf05f3dd5421a6528c2bffa947b3ba |
| runs/car_interior_suv/preprocess/car_interior_suv/cropped.png | b6c159d17e5ed85b04d91298b6d9fc3cbe12c9dbed583b494edbd1112792d856 |
| runs/car_interior_suv/preprocess/car_interior_suv/meta.json | de66d7826a312873c9eb5f112dd12b504f15ff2245e75b4b6b98177732f44e96 |
| runs/site_photo_department_store/detail.json | 4cdefb80ec8eb4592ac8a7c087799af9835f4d5567a6a80e719c82b116a63737 |
| runs/site_photo_department_store/preprocess/site_photo_department_store/cropped.png | 5765db2f8722caee7efb8ef5b4506606811dda54f018b6326339a7dde4165c03 |
| runs/site_photo_department_store/preprocess/site_photo_department_store/meta.json | 63a93695562f14939c0884c3480500826f0ee92f68ff23afa5d83f376a0c1cc4 |
| runs/site_photo_gym/detail.json | adce61181903a86431d929ff7a28e5789e7a8811257bae0b08d7aedf29e55214 |
| runs/site_photo_gym/preprocess/site_photo_gym/cropped.png | c8b707e7d53a6f0e00a0a08a9ac387f2b49da64b07d7df43756521bd9268f4f7 |
| runs/site_photo_gym/preprocess/site_photo_gym/meta.json | 9431b054688e7350c4444663aee6aadcfb99abed78fe58e4bd683a71e3f957af |
| runs/site_photo_restaurant/detail.json | a1b7088f47ce11c0f7b2a2f34885298ac668ec682d6e1e372f02c09c906efbd8 |
| runs/site_photo_restaurant/preprocess/site_photo_restaurant/cropped.png | 15c792d48997e138cec13286045aca0310468cc2be1ec8ec1806bfaa3e27792d |
| runs/site_photo_restaurant/preprocess/site_photo_restaurant/meta.json | 7d0d2b3652b029b39354a0ee14ba8b2acdc39a15d17a6fb13fd9f8c2fadca3f3 |
| runs/stairwell_tiled/detail.json | 6ce77e6908180a335ff3acfd79c1ab6ae13bd83cbb09e3eafac688b2f3395a63 |
| runs/stairwell_tiled/preprocess/stairwell_tiled/cropped.png | de034d96e947d590bdd42dadb55161199837117f0732d603cf689183e5a03b9e |
| runs/stairwell_tiled/preprocess/stairwell_tiled/meta.json | b93038164d6629609535cc89c003df13c9b1a4294b321316da025562a938e594 |
| tables.md | 7a3022bf967d229069e15b2ec9370a2450751f13fc57ff2bd84990983ef5460d |

共 71 個檔案。

