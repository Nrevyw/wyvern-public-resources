import seaborn as sns

MAX_DEPTH = -30
MIN_DEPTH = 0

WYV_PALETTE_VALUES = [
    "#3b26f9",
    "#ff4848",
    "#F4037B",
    "#322c56",
    "#000000",
]
WYV_PALETTE = sns.color_palette(WYV_PALETTE_VALUES, len(WYV_PALETTE_VALUES))

# This is Dragonette-003's band names. Dragonette-002 and other satellites w/ the
# extended spectral range product will have band centres that differ by +/- 1nm.
# Keeping the band names consistent is important for processing & feature engineering.
# NOTE: Not currently used but important if doing more feature engineering.
FIXED_BAND_NAMES = [
    "Band_445",
    "Band_465",
    "Band_480",
    "Band_489",
    "Band_502",
    "Band_509",
    "Band_519",
    "Band_534",
    "Band_549",
    "Band_569",
    "Band_584",
    "Band_600",
    "Band_614",
    "Band_635",
    "Band_650",
    "Band_660",
    "Band_670",
    "Band_680",
    "Band_690",
    "Band_700",
    "Band_712",
    "Band_721",
    "Band_734",
    "Band_750",
    "Band_765",
    "Band_782",
    "Band_800",
    "Band_815",
    "Band_832",
    "Band_850",
    "Band_870",
]

# Feature engineering. These ratios correspond with the top 10 highest correlated
# ratios with depth on Dragonette-002. D3 ratios have been slightly shifted, and
# ratios w/ band centres available on D1 have been kept.
RUN_FEATURE_ENGINEERING = True
D1_BAND_RATIOS = [
    ("Band_503", "Band_570"),
    ("Band_519", "Band_570"),
    ("Band_503", "Band_549"),
    ("Band_570", "Band_690"),
    ("Band_584", "Band_690"),
    ("Band_570", "Band_734"),
    ("Band_570", "Band_722"),
]
D2_BAND_RATIOS = [
    ("Band_502", "Band_569"),
    ("Band_489", "Band_569"),
    ("Band_519", "Band_569"),
    ("Band_502", "Band_549"),
    ("Band_489", "Band_549"),
    ("Band_569", "Band_690"),
    ("Band_569", "Band_832"),
    ("Band_584", "Band_690"),
    ("Band_569", "Band_734"),
    ("Band_569", "Band_721"),
]

D3_BAND_RATIOS = [
    ("Band_503", "Band_569"),
    ("Band_490", "Band_569"),
    ("Band_519", "Band_569"),
    ("Band_503", "Band_550"),
    ("Band_490", "Band_550"),
    ("Band_569", "Band_689"),
    ("Band_569", "Band_832"),
    ("Band_585", "Band_689"),
    ("Band_569", "Band_734"),
    ("Band_569", "Band_722"),
]

# Denotes the root name of the experiment. Will generate a subfolder with this name
# containing run results. If you want to change something up and experiment, modify
# this to keep everything clean.
# Yes, I know I should really just use MLFlow or something...
EXPERIMENT_ROOT_NAME = "wyvern_baseline_bathy_simple_ratios_final_baseline"

# This is a list of experiments to compute. Results of each experiment will be available
# in the run subfolder.
EXPERIMENTS = {
    "wyvern_d1_molokai_single_image": {
        "category": "single_image",  # Overarching category, single-image or multi-image
        "group": "drag_001_molokai",  # Subgroup for comparing Sentinel-2 vs. Wyvern
        "image_type": "wyvern",  # `wyvern` or `sentinel-2`
        "satellite": "drag001",  # Satellite name, either `drag00X` or `sentinel2`
        "rgb_render_indices": [
            10,
            5,
            0,
        ],  # Band indicies (from 0) for a pretty RGB preview
        "ratios": D1_BAND_RATIOS,  # Simple ratio feature engineering
        "train_test_images": [
            # List of images + labels + sampling AOIs for the train/test set
            {
                "image": "wyvern_dragonette-001_20250101T201001_5dc97ba2.tiff",
                "labels": "wyvern_dragonette-001_20250101T201001_5dc97ba2_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-001_20250101T201001_5dc97ba2_traintest.geojson",
            }
        ],
        "validation_images": [
            # List of images + labels + sampling AOIs for the validation set
            {
                "image": "wyvern_dragonette-001_20250101T201001_5dc97ba2.tiff",
                "labels": "wyvern_dragonette-001_20250101T201001_5dc97ba2_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-001_20250101T201001_5dc97ba2_validation.geojson",
            }
        ],
    },
    "sentinel2_d1_molokai_single_image": {
        "category": "single_image",
        "group": "drag_001_molokai",
        "image_type": "sentinel2",
        "satellite": "sentinel2",
        "rgb_render_indices": [4, 3, 2],  # Sentinel-2 RGB bands
        "ratios": [],
        "train_test_images": [
            {
                "image": "S2A_MSIL2A_20250114T210921_R057_T04QFJ_20250114T231353.tiff",
                "labels": "S2A_MSIL2A_20250114T210921_R057_T04QFJ_20250114T231353_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-001_20250101T201001_5dc97ba2_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "S2A_MSIL2A_20250114T210921_R057_T04QFJ_20250114T231353.tiff",
                "labels": "S2A_MSIL2A_20250114T210921_R057_T04QFJ_20250114T231353_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-001_20250101T201001_5dc97ba2_validation.geojson",
            }
        ],
    },
    "wyvern_d2_molokai_single_image": {
        "category": "single_image",
        "group": "drag_002_molokai",
        "image_type": "wyvern",
        "satellite": "drag002",
        "rgb_render_indices": [10, 5, 0],
        "ratios": D2_BAND_RATIOS,
        "train_test_images": [
            {
                "image": "wyvern_dragonette-002_20250225T004037_4788dc6b.tiff",
                "labels": "wyvern_dragonette-002_20250225T004037_4788dc6b_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-002_20250225T004037_4788dc6b_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "wyvern_dragonette-002_20250225T004037_4788dc6b.tiff",
                "labels": "wyvern_dragonette-002_20250225T004037_4788dc6b_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-002_20250225T004037_4788dc6b_validation.geojson",
            }
        ],
    },
    "wyvern_d2_molokai_single_image_10m_res": {
        "category": "single_image",
        "group": "drag_002_molokai",
        "image_type": "wyvern",
        "satellite": "drag002",
        "rgb_render_indices": [10, 5, 0],
        "ratios": D2_BAND_RATIOS,
        "train_test_images": [
            {
                "image": "wyvern_dragonette-002_20250225T004037_4788dc6b_10m_res.tif",
                "labels": "wyvern_dragonette-002_20250225T004037_4788dc6b_10m_res_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-002_20250225T004037_4788dc6b_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "wyvern_dragonette-002_20250225T004037_4788dc6b.tiff",
                "labels": "wyvern_dragonette-002_20250225T004037_4788dc6b_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-002_20250225T004037_4788dc6b_validation.geojson",
            }
        ],
    },
    "sentinel2_d2_molokai_single_image": {
        "category": "single_image",
        "group": "drag_002_molokai",
        "image_type": "sentinel2",
        "satellite": "sentinel2",
        "rgb_render_indices": [4, 3, 2],  # Sentinel-2 RGB bands
        "ratios": [],
        "train_test_images": [
            {
                "image": "S2B_MSIL2A_20250228T210929_R057_T04QGJ_20250228T230046.tiff",
                "labels": "S2B_MSIL2A_20250228T210929_R057_T04QGJ_20250228T230046_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-002_20250225T004037_4788dc6b_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "S2B_MSIL2A_20250228T210929_R057_T04QGJ_20250228T230046.tiff",
                "labels": "wS2B_MSIL2A_20250228T210929_R057_T04QGJ_20250228T230046_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-002_20250225T004037_4788dc6b_validation.geojson",
            }
        ],
    },
    "wyvern_d3_molokai_single_image": {
        "category": "single_image",
        "group": "drag_003_molokai",
        "image_type": "wyvern",
        "satellite": "drag003",
        "rgb_render_indices": [10, 5, 0],
        "ratios": D3_BAND_RATIOS,
        "train_test_images": [
            {
                "image": "wyvern_dragonette-003_20250508T203730_3cb1306b.tiff",
                "labels": "wyvern_dragonette-003_20250508T203730_3cb1306b_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20250508T203730_3cb1306b_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "wyvern_dragonette-003_20250508T203730_3cb1306b.tiff",
                "labels": "wyvern_dragonette-003_20250508T203730_3cb1306b_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20250508T203730_3cb1306b_validation.geojson",
            }
        ],
    },
    "sentinel2_d3_molokai_single_image": {
        "category": "single_image",
        "group": "drag_003_molokai",
        "image_type": "sentinel2",
        "satellite": "sentinel2",
        "rgb_render_indices": [4, 3, 2],  # Sentinel-2 RGB bands
        "ratios": [],
        "train_test_images": [
            {
                "image": "S2B_MSIL2A_20250228T210929_R057_T04QFJ_20250228T230046.tiff",
                "labels": "S2B_MSIL2A_20250228T210929_R057_T04QFJ_20250228T230046_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20250508T203730_3cb1306b_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "S2B_MSIL2A_20250228T210929_R057_T04QFJ_20250228T230046.tiff",
                "labels": "S2B_MSIL2A_20250228T210929_R057_T04QFJ_20250228T230046_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20250508T203730_3cb1306b_validation.geojson",
            }
        ],
    },
    "wyvern_d3_maui_single_image": {
        "category": "single_image",
        "group": "drag_003_maui",
        "image_type": "wyvern",
        "satellite": "drag003",
        "rgb_render_indices": [10, 5, 0],
        "ratios": D3_BAND_RATIOS,
        "train_test_images": [
            {
                "image": "wyvern_dragonette-003_20241206T203812_64e116d6.tiff",
                "labels": "wyvern_dragonette-003_20241206T203812_64e116d6_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20241206T203812_64e116d6_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "wyvern_dragonette-003_20241206T203812_64e116d6.tiff",
                "labels": "wyvern_dragonette-003_20241206T203812_64e116d6_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20241206T203812_64e116d6_validation.geojson",
            }
        ],
    },
    "sentinel2_d3_maui_single_image": {
        "category": "single_image",
        "group": "drag_003_maui",
        "image_type": "sentinel2",
        "satellite": "sentinel2",
        "rgb_render_indices": [4, 3, 2],  # Sentinel-2 RGB bands
        "ratios": [],
        "train_test_images": [
            {
                "image": "S2A_MSIL2A_20241205T210921_R057_T04QGJ_20241205T231445.tiff",
                "labels": "S2A_MSIL2A_20241205T210921_R057_T04QGJ_20241205T231445_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20241206T203812_64e116d6_traintest.geojson",
            }
        ],
        "validation_images": [
            {
                "image": "S2A_MSIL2A_20241205T210921_R057_T04QGJ_20241205T231445.tiff",
                "labels": "S2A_MSIL2A_20241205T210921_R057_T04QGJ_20241205T231445_ground_truth.tif",
                "label_aoi": "wyvern_dragonette-003_20241206T203812_64e116d6_validation.geojson",
            }
        ],
    },
}
