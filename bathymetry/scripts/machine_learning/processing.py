import numpy as np
from sklearn.metrics import r2_score, root_mean_squared_error, mean_absolute_error

from config import MAX_DEPTH, MIN_DEPTH


def process_arrays(
    image_arr: np.ndarray, label_arr: np.ndarray, filter_depth=True, bands=[], ratios=[]
) -> np.ndarray:
    """Processes image array and label array into a flattened representation for
    traditional ML training.

    NOTE: This function is BRUTAL and will be improved in short order. The
    feature engineering needs to be moved out to a separate function and
    column names/converting to a dataframe needs to be done.

    Args:
        image_arr (np.ndarray): Image array in [BAND, X, Y] shape.
        label_arr (np.ndarray): Label array in [X, Y] shape.
        filter_depth (bool, optional): Filters depths to configured range if True. Defaults to True.
        bands (list, optional): List of band names. Defaults to [].
        ratios (list, optional): List of ratios to compute. Defaults to [].

    Returns:
        np.ndarray: Array containing bands, ratios, and label in that order.
    """
    # Flatten/reshape
    img_shp = image_arr.shape
    image_reshaped = image_arr.reshape((img_shp[0], img_shp[1] * img_shp[2]))
    label_reshaped = label_arr.reshape((1, img_shp[1] * img_shp[2]))

    # Add feature engineering
    calcd_ratios, extra_feat_names = [], []
    if len(ratios) > 0:
        for band_0, band_1 in ratios:
            calcd_ratios.append(
                image_reshaped[bands.index(band_0)]
                / image_reshaped[bands.index(band_1)]
            )
            extra_feat_names.append(f"ratio_{band_0}_{band_1}")
        image_reshaped = np.append(image_reshaped, np.array(calcd_ratios), axis=0)

    # Append labels to image array
    ds = np.append(image_reshaped, label_reshaped, axis=0)

    # Filter for depths greater than -50 (removes NaNs) and less than 0 (removes above water values)
    if filter_depth:
        filtered_ds = ds[
            :, (ds[-1] > MAX_DEPTH) & (ds[-1] < MIN_DEPTH) & (ds[0] > -100)
        ]
        filtered_ds = np.swapaxes(filtered_ds, 0, -1)
        return filtered_ds, extra_feat_names
    else:
        return np.swapaxes(ds, 0, -1), extra_feat_names


def assess_model_performance(
    experiment_name: str,
    y_test: np.ndarray,
    test_preds: np.ndarray,
    y_val: np.ndarray,
    val_preds: np.ndarray,
) -> dict:
    """Assesses model performance across depth ranges. Generates dictionary
    containing performance values for the model across both the test and
    validation sets.

    Args:
        experiment_name (str): Name of experiment
        y_test (np.ndarray): Array of test set ground truth
        test_preds (np.ndarray): Array of test set predictions
        y_val (np.ndarray): Array of validation set ground truth
        val_preds (np.ndarray): Array of validation set predictions

    Returns:
        dict: Dictionary containing all performance values
    """
    return {
        "experiment": experiment_name,
        "test": {
            "samples": len(test_preds),
            "r2": r2_score(y_test, test_preds),
            "rmse": root_mean_squared_error(y_test, test_preds),
            "mae": mean_absolute_error(y_test, test_preds),
            "<20m": {
                "samples": len(test_preds[y_test > -20]),
                "r2": r2_score(y_test[y_test > -20], test_preds[y_test > -20]),
                "rmse": root_mean_squared_error(
                    y_test[y_test > -20], test_preds[y_test > -20]
                ),
                "mae": mean_absolute_error(
                    y_test[y_test > -20], test_preds[y_test > -20]
                ),
            },
            ">20m": {
                "samples": len(test_preds[test_preds < -20]),
                "r2": r2_score(y_test[test_preds < -20], test_preds[test_preds < -20]),
                "rmse": root_mean_squared_error(
                    y_test[test_preds < -20], test_preds[test_preds < -20]
                ),
                "mae": mean_absolute_error(
                    y_test[test_preds < -20], test_preds[test_preds < -20]
                ),
            },
        },
        "validation": {
            "samples": len(val_preds),
            "r2": r2_score(y_val, val_preds),
            "rmse": root_mean_squared_error(y_val, val_preds),
            "mae": mean_absolute_error(y_val, val_preds),
            "<20m": {
                "samples": len(val_preds[y_val > -20]),
                "r2": r2_score(y_val[y_val > -20], val_preds[y_val > -20]),
                "rmse": root_mean_squared_error(
                    y_val[y_val > -20], val_preds[y_val > -20]
                ),
                "mae": mean_absolute_error(y_val[y_val > -20], val_preds[y_val > -20]),
            },
            ">20m": {
                "samples": len(val_preds[y_val < -20]),
                "r2": r2_score(y_val[y_val < -20], val_preds[y_val < -20]),
                "rmse": root_mean_squared_error(
                    y_val[y_val < -20], val_preds[y_val < -20]
                ),
                "mae": mean_absolute_error(y_val[y_val < -20], val_preds[y_val < -20]),
            },
        },
    }
