import os
import sys
import json
import logging
import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import xgboost as xgb
import lightgbm as lgb
import seaborn as sns

from rasterio.windows import from_bounds
from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from datetime import datetime

from config import EXPERIMENT_ROOT_NAME, EXPERIMENTS, WYV_PALETTE
from plots import (
    render_imagery_and_labels,
    render_histogram,
    render_predictions,
    render_validation_performance,
)
from processing import process_arrays, assess_model_performance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def run_ml_experiment(
    model: BaseEstimator,
    satellite: str,
    model_name: str,
    image_path: str,
    label_path: str,
    train_aoi_path: str,
    val_aoi_path: str,
    rgb_render_indices: list[int],
    experiment_name: str,
    working_dir: str = "./results",
    ratios: list[tuple[str, str]] = [],
) -> dict:
    """Runs an experiment for the provided model and datasets

    TODO: Support multiple images for train/test and validation
    TODO: Better feature engineering

    Args:
        model (BaseEstimator): Regression model
        satellite (str): Satellite name, not currently used.
        model_name (str): Name of the model
        image_path (str): Path to image for train/test/validation
        label_path (str): Path to labels/ground truth
        train_aoi_path (str): Path to train/test AOI
        val_aoi_path (str): Path to validation AOI
        rgb_render_indices (list[int]): List of array indices for RGB rendering
        experiment_name (str): Name of this experiment
        working_dir (str, optional): Directory to export results to. Defaults to "./results".
        ratios (list[tuple[str, str]], optional): Custom ratios to apply to dataset. Defaults to [].

    Returns:
        dict: Experiment results
    """
    logging.info("Loading AOIs and configuring working directory!")
    working_folder = working_dir
    os.makedirs(working_folder, exist_ok=True)
    train_aoi_df = gpd.read_file(train_aoi_path)
    val_aoi_df = gpd.read_file(val_aoi_path)

    logging.info("Reading image files")
    image_file = rasterio.open(image_path)
    labels_file = rasterio.open(label_path)

    logging.info("Configuring windows for loading imagery")
    train_test_window = from_bounds(
        *train_aoi_df.total_bounds, transform=image_file.transform
    )
    train_test_label_window = from_bounds(
        *train_aoi_df.total_bounds, transform=labels_file.transform
    )
    val_window = from_bounds(*val_aoi_df.total_bounds, transform=image_file.transform)
    val_label_window = from_bounds(
        *val_aoi_df.total_bounds, transform=labels_file.transform
    )

    logging.info("Loading image arrays for train/test and validation")
    train_test_arr = image_file.read(window=train_test_window)
    train_test_label_arr = labels_file.read(window=train_test_label_window)

    val_arr = image_file.read(window=val_window)
    val_label_arr = labels_file.read(window=val_label_window)
    logging.info(
        f"Train/Test image shape: {train_test_arr.shape}; Labels shape: {train_test_label_arr.shape}"
    )
    logging.info(
        f"Val image shape: {val_arr.shape}; Labels shape: {val_label_arr.shape}"
    )

    logging.info("Rendering imagery!")
    render_imagery_and_labels(
        train_arr=train_test_arr[rgb_render_indices],
        train_labels=train_test_label_arr,
        val_arr=val_arr[rgb_render_indices],
        val_labels=val_label_arr,
        title=f"{experiment_name}",
        write_path=f"{working_folder}/image_render.jpg",
    )

    logging.info("Pre-processing arrays!")
    filtered_train_test_ds, extra_cols = process_arrays(
        train_test_arr,
        train_test_label_arr,
        bands=image_file.descriptions,
        ratios=ratios,
    )
    filtered_val_ds, extra_cols = process_arrays(
        val_arr,
        val_label_arr,
        bands=image_file.descriptions,
        ratios=ratios,
    )
    logging.info(
        f"Train/Test Shape: {filtered_train_test_ds.shape}, Val Shape: {filtered_val_ds.shape}"
    )

    if model_name == "svm" and filtered_train_test_ds.shape[0] > 50000:
        logging.info("Downsampling dataset for SVM training!")
        downsample_index = np.random.choice(
            filtered_train_test_ds.shape[0], 50000, replace=False
        )
        filtered_train_test_ds = filtered_train_test_ds[downsample_index]

    logging.info("Rendering diagnostic plots!")
    render_histogram(
        depth_arr=filtered_train_test_ds[:, -1],
        title=f"{experiment_name} - Train/Test Histogram, Depth",
        write_path=f"{working_folder}/train_test_histogram.jpg",
    )
    render_histogram(
        depth_arr=filtered_val_ds[:, -1],
        title=f"{experiment_name} - Validation Histogram, Depth",
        write_path=f"{working_folder}/validation_histogram.jpg",
    )

    X_train, X_test, y_train, y_test = train_test_split(
        filtered_train_test_ds[:, 0:-1], filtered_train_test_ds[:, -1], random_state=0
    )

    logging.info("Training model!")
    model.fit(X_train, y_train)

    # Predict & Score model
    test_preds = model.predict(X_test)
    val_preds = model.predict(filtered_val_ds[:, 0:-1])

    if model_name == "lightgbm" or model_name == "xgboost":
        sns.set_style("dark")
        sns.set_context("notebook", font_scale=1.1)
        sns.set_palette(WYV_PALETTE)

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        feat_names = list(image_file.descriptions) + extra_cols
        df = pd.DataFrame.from_records(
            zip(feat_names, model.feature_importances_),
            columns=["feature", "importance"],
        )
        df.sort_values("importance", ascending=False, inplace=True)

        sns.barplot(df.iloc[0:10], x="importance", y="feature")
        ax.set_xlabel("Feature Importance")
        ax.set_ylabel("Features")
        plt.suptitle(f"{experiment_name} - {model_name}\nFeature Importance (Top 10)")
        plt.tight_layout()
        plt.savefig(f"{working_folder}/feature_importance.jpg", dpi=200)
        plt.clf()
        sns.reset_defaults()

    logging.info("Writing performance results...")
    performance_results = assess_model_performance(
        experiment_name, y_test, test_preds, filtered_val_ds[:, -1], val_preds
    )
    with open(f"{working_folder}/results.json", "w") as f:
        f.write(json.dumps(performance_results, indent=4))

    logging.info("Rendering validation predictions...")
    val_img_preds, val_img_actuals = render_predictions(
        img_arr=val_arr,
        label_arr=val_label_arr,
        model=model,
        nan_value=image_file.nodata,
        title=f"{experiment_name} - Validation Predictions vs. Ground Truth",
        write_path=f"{working_folder}/val_predictions.jpg",
        bands=image_file.descriptions,
        ratios=ratios,
    )

    logging.info("Saving predictions!")
    with open(f"{working_folder}/val_true.npy", "wb") as f:
        np.save(f, val_img_actuals)

    with open(f"{working_folder}/val_preds.npy", "wb") as f:
        np.save(f, val_img_preds)

    logging.info("Rendering validation performance...")
    render_validation_performance(
        y_true=filtered_val_ds[:, -1],
        y_pred=val_preds,
        title=f"{experiment_name} - Validation Set Performance",
        write_path=f"{working_folder}/validation_performance.jpg",
    )

    return performance_results


def main():
    """Runs all ML experiments and exports to standard directory structure."""
    plt.ioff()
    outer_working_folder = f"data/results/{EXPERIMENT_ROOT_NAME}/run_{datetime.now().strftime('%Y%m%dT%H%M%S')}/"
    os.makedirs(outer_working_folder, exist_ok=True)
    results_dict = {}
    for experiment_name, experiment in EXPERIMENTS.items():
        for model_name, model in [
            ("random_forest", RandomForestRegressor(n_jobs=-1, random_state=42)),
            ("svm", Pipeline([("scaler", StandardScaler()), ("svm", SVR())])),
            ("lightgbm", lgb.LGBMRegressor(random_state=42)),
            ("xgboost", xgb.XGBRegressor(random_state=42)),
        ]:
            logging.info(
                f"Running experiment: {experiment_name} with model: {model_name}"
            )
            combined_name = f"{experiment_name}_{model_name}"
            experiment_working_folder = f"{outer_working_folder}{combined_name}"
            results = run_ml_experiment(
                model=model,
                satellite=experiment["satellite"],
                model_name=model_name,
                image_path="data/datasets/"
                + experiment["train_test_images"][0]["image"],
                label_path="data/datasets/"
                + experiment["train_test_images"][0]["labels"],
                train_aoi_path="data/aois/"
                + experiment["train_test_images"][0]["label_aoi"],
                val_aoi_path="data/aois/"
                + experiment["validation_images"][0]["label_aoi"],
                rgb_render_indices=experiment["rgb_render_indices"],
                experiment_name=combined_name,
                working_dir=experiment_working_folder,
                ratios=experiment["ratios"],
            )
            results_dict[combined_name] = results | experiment

    logging.info("Writing out results!")
    with open(f"{outer_working_folder}results.json", "w") as f:
        json.dump(results_dict, f)


if __name__ == "__main__":
    main()
