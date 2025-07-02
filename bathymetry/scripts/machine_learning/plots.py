import logging
import numpy as np
import matplotlib.pyplot as plt

from sklearn.base import BaseEstimator
from sklearn.metrics import r2_score, PredictionErrorDisplay, root_mean_squared_error

from config import MAX_DEPTH, MIN_DEPTH
from utils import min_max_normalize
from processing import process_arrays


def render_imagery_and_labels(
    train_arr: np.ndarray,
    train_labels: np.ndarray,
    val_arr: np.ndarray,
    val_labels: np.ndarray,
    title: str,
    write_path: str,
):
    """Renders a plot containing an RGB preview image + label preview image for
    both the train/test and validation set.

    Args:
        train_arr (np.ndarray): RGB image array, [Channel (RGB), X, Y] shape
        train_labels (np.ndarray): Label array [X, Y] shape
        val_arr (np.ndarray): RGB image array, [Channel (RGB), X, Y] shape
        val_labels (np.ndarray): Label array [X, Y] shape
        title (str): Title for the plot
        write_path (str): Path to write the plot to
    """
    logging.info("Setting up plot and image arrays!")
    fig, axs = plt.subplots(2, 2, figsize=(10, 6))
    traintest_img_arr = min_max_normalize(
        np.swapaxes(np.swapaxes(train_arr, 0, -1), 0, 1)
    )
    val_img_arr = min_max_normalize(np.swapaxes(np.swapaxes(val_arr, 0, -1), 0, 1))

    logging.info("Plotting train/test image & labels")
    axs[0, 0].imshow(traintest_img_arr * 1.5)
    axs[0, 0].set_title("Train/Test - Image (RGB)")

    # We remove labels with a height greater than 10m, that's way too high for us
    train_test_depth = np.where(train_labels > 10, np.nan, train_labels)
    train_test_plt = axs[0, 1].imshow(
        train_test_depth[0], norm="linear", vmin=-50, vmax=10
    )
    axs[0, 1].set_title("Train/Test - Water Depth (meters)")
    cbar = plt.colorbar(train_test_plt, ax=axs[0, 1], label="Elevation (m)")

    logging.info("Plotting validation image & labels")
    axs[1, 0].imshow(val_img_arr * 1.5)  # 1.5 brightens the image a bit
    axs[1, 0].set_title("Validation - Image (RGB)")

    val_depth = np.where(val_labels > 10, np.nan, val_labels)
    val_plt = axs[1, 1].imshow(val_depth[0], norm="linear", vmin=-50, vmax=10)
    axs[1, 1].set_title("Validation - Water Depth (meters)")
    cbar = plt.colorbar(val_plt, ax=axs[1, 1], label="Elevation (m)")

    logging.info("Finalizing layout and saving figure to disk!")
    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(write_path, dpi=150)


def render_validation_performance(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str,
    write_path: str,
    downsample: int = 10000,
):
    """Renders PredictionErrorDisplays for provided ground truth and predictions.

    Downsamples chart if needed, since it can be hard to read with lots of points.

    Args:
        y_true (np.ndarray): Ground truth values
        y_pred (np.ndarray): Prediction values
        title (str): Title for plot
        write_path (str): Path to write plot to
        downsample (int, optional): Number of points to downsample to. Defaults to 10000.
    """
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))

    if downsample > 0 and len(y_pred) > downsample:
        index = np.random.choice(y_true.shape[0], downsample, replace=False)
        pred_err = PredictionErrorDisplay(y_true=y_true[index], y_pred=y_pred[index])
    else:
        pred_err = PredictionErrorDisplay(y_true=y_true, y_pred=y_pred)

    # Actually plot prediction error
    pred_err.plot(ax=axs[0], kind="actual_vs_predicted", scatter_kwargs={"alpha": 0.15})
    pred_err.plot(
        ax=axs[1], kind="residual_vs_predicted", scatter_kwargs={"alpha": 0.15}
    )

    r_2 = r2_score(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)

    axs[0].set_title("Actual vs. Predicted")
    axs[1].set_title("Residuals vs. Predicted")
    full_title = (
        f"{title}"
        f"\nNumber of points: {y_true.shape[0]:,}"
        f"\nR2: {round(r_2, 6)}, "
        f"RMSE: {round(rmse, 6)} m"
    )
    if downsample > 0:
        full_title = (
            full_title
            + f"\n\n Note: Points are downsampled ({downsample} points) for rendering on chart"
        )

    plt.suptitle(full_title)
    plt.tight_layout()
    plt.savefig(write_path, dpi=150)


def render_histogram(depth_arr: np.ndarray, title: str, write_path: str):
    """Renders a histogram chart for depth values

    Args:
        depth_arr (np.ndarray): Array of depth values to bin/plot
        title (str): Title for plot
        write_path (str): Path to write plot to
    """
    counts, bins = np.histogram(depth_arr, bins=60)
    fig, axs = plt.subplots(1, 1)
    axs.hist(bins[:-1], bins, weights=counts)
    plt.title(title)
    plt.savefig(write_path, dpi=150)


def render_predictions(
    img_arr: np.ndarray,
    label_arr: np.ndarray,
    model: BaseEstimator,
    nan_value: float,
    bands: list[str],
    ratios: list[tuple[str, str]],
    title: str,
    write_path: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Renders model predictions as an image

    Args:
        img_arr (np.ndarray): Raw image array
        label_arr (np.ndarray): Raw labels array
        model (BaseEstimator): Sklearn-compatible regression model
        nan_value (float): NaN value
        bands (list[str]): List of band names
        ratios (list[tuple[str, str]]): List of ratios, needed for feature engineering
        title (str): Title of plot
        write_path (str): Path to write plot to

    Returns:
        tuple[np.ndarray, np.ndarray]: Predictions and labels for later use.
    """
    # Process arrays
    img_shp = img_arr.shape
    processed_img, extra_cols = process_arrays(
        img_arr, label_arr, -9999, filter_depth=False, bands=bands, ratios=ratios
    )

    # Predict
    val_img_preds = model.predict(processed_img[:, 0:-1])
    val_img_preds.shape

    # Reconstruct arrays
    val_pred_img = val_img_preds.reshape((img_shp[1], img_shp[2]))
    empty_arr = np.empty((img_shp[1], img_shp[2]))
    empty_arr[:] = np.nan
    val_pred_img = np.where(
        (label_arr[0] > MAX_DEPTH) & (label_arr[0] < MIN_DEPTH) & (img_arr[0] > -100),
        val_pred_img,
        empty_arr,
    )
    val_actual_img = np.where(
        (label_arr[0] > MAX_DEPTH) & (label_arr[0] < MIN_DEPTH) & (img_arr[0] > -100),
        label_arr,
        empty_arr,
    )

    fig, axs = plt.subplots(1, 3, figsize=(22, 6))
    pred_img = axs[0].imshow(val_pred_img)
    axs[0].set_title("Predictions")
    plt.colorbar(pred_img, ax=axs[0], label="Elevation (m)")

    resid_img = axs[1].imshow(val_pred_img - val_actual_img[0])
    axs[1].set_title("Residuals")
    plt.colorbar(resid_img, ax=axs[1], label="Elevation (m)")

    act_img = axs[2].imshow(val_actual_img[0])
    axs[2].set_title("Actuals")
    plt.colorbar(act_img, ax=axs[2], label="Elevation (m)")

    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(write_path, dpi=300)

    return (val_pred_img, val_actual_img[0])
