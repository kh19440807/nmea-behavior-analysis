# Overview

## 1. Motivation
GNSS spoofing and jamming incidents have been increasingly reported in maritime, robotics, and autonomous systems.
However, many existing countermeasures focus on hardware-level defenses or cryptographic authentication,
which are not always available in low-cost or legacy GNSS receivers.

This project is motivated by a simple question:
can anomalous GNSS behavior be identified by analyzing receiver output behavior alone,
using only standard NMEA logs recorded during operation?

## 2. Problem Statement
Rule-based anomaly detection using GNSS metrics such as satellite count, HDOP, or C/N₀
can detect obvious failures, but often fails in more subtle spoofing scenarios
where signals remain strong and navigation solutions appear nominal.

The challenge addressed here is distinguishing spoofed and unspoofed GNSS behavior
in offline NMEA logs when:
- signal strength appears normal
- standard quality metrics do not trigger alarms
- position and velocity remain superficially plausible

## 3. Approach
This project explores a hybrid analysis approach combining:

1. Rule-based indicators:
   Simple heuristics based on time continuity, position jumps, velocity consistency,
   and signal quality transitions.

2. Statistical and machine-learning-based classification:
   Features derived from NMEA time series (e.g. speed statistics, C/N₀ distributions,
   temporal consistency metrics) are used to train classifiers that capture
   behavioral patterns beyond fixed thresholds.

The intent is not to replace rule-based checks,
but to evaluate whether data-driven methods can complement them
in post-event analysis.

## 4. Dataset and Evaluation
Model training and evaluation are performed using the publicly available [MARSIM dataset](https://zenodo.org/records/8202802),
which contains both spoofed and unspoofed maritime GNSS recordings.

Each NMEA log is processed offline to extract time-series features.
Models are evaluated using standard classification metrics
(accuracy, precision, recall, F1-score) on balanced subsets of the dataset.

This evaluation is intended to assess discriminative capability,
not operational detection performance.

## 5. Observations
Initial experiments indicate that:
- Signal strength metrics alone are insufficient to distinguish spoofing
- Velocity and heading consistency provide stronger behavioral signals
- Statistical distributions over time (rather than instantaneous values)
  are more informative than single-sample thresholds

These observations support the hypothesis that
GNSS spoofing can manifest as subtle behavioral inconsistencies
even when traditional quality indicators remain nominal.

## 6. Limitations
This project has several important limitations:

- Analysis is performed offline on recorded logs
- Results depend on the characteristics of the MARSIM dataset
- No real-time constraints or latency considerations are addressed
- No claims are made regarding detection reliability in operational environments

False positives and false negatives are expected,
and results should not be interpreted as safety guarantees.

## 7. Intended Use
This repository is intended for:
- Research and technical exploration
- Post-event GNSS log analysis
- Reproducible experimentation using public datasets

It is not intended for:
- Real-time spoofing detection
- Safety-critical navigation systems
- Commercial or operational deployment
