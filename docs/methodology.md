# Research Methodology

## Data preparation

Synthetic data is generated from labeled feature profiles and Gaussian noise. Missing values are imputed by median for numeric fields and most frequent value for protocol type. Numeric features are standardized inside a fitted column transformer. Uploads must identify a supported label column.

The pipeline is fitted only after data partitions are constructed for the research workflow, preventing preprocessing parameters from leaking across the held-out class in the zero-day experiment. Uploaded cross-platform datasets should be mapped to supported feature names.

## Federated training

Each communication round copies the current global SGD coefficients to participating simulated clients. Each client trains on its local partition for the configured number of epochs. Aggregation is sample-count weighted, with an additional inverse-error factor:

$$w_i \propto n_i \left(1 + L_i\right)^{-1}$$

The previous global coefficients are replaced by the weighted mean. Accuracy is measured on the complete local simulation corpus because this implementation executes in memory; no raw traffic leaves the simulated client partition boundary.

## Adaptation

A round-level client filter compares recent loss with round progress. If the sensitivity threshold is exceeded, selected clients may skip a round. This is a simple heuristic rather than a validated online drift detector. A user can increase communication rounds to retrain after observed drift.

## Zero-day detection

For a held-out family, the anomaly score is `1 - maximum probability`. The threshold and predictions are evaluated against binary ground truth where held-out equals anomalous. The confusion matrix is anchored in that binary evaluation. Low confidence from an uncertain model is not synonymous with semantic novelty.

## Evaluation limitations

Synthetic class separation may produce optimistic ROC-AUC values. Results depend on seed, partition, threshold, calibration, missing values, and class balance. Precision and recall are threshold-dependent. The implementation must be validated with independently sourced and lawfully redistributable benchmark datasets before research claims are made.
