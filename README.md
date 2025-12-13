# GNSS NMEA Behavior Analysis (Experimental Prototype)

This repository contains an experimental, non-commercial research prototype for analyzing GNSS behavior from offline NMEA logs.

The purpose of this project is technical exploration and validation, focusing on whether machine-learning-based approaches can distinguish spoofed vs. unspoofed GNSS behavior in scenarios where traditional rule-based checks are insufficient. The focus is on post-event analysis rather than operational detection.

## Key Characteristics
- Offline analysis of recorded NMEA logs
- ML models trained and evaluated using the public MARSIM maritime spoofing dataset
- Comparison between:
  - traditional rule-based anomaly indicators
  - statistical / machine-learning-based classification
- Visualization of:
  - GNSS signal quality (C/N₀)
  - velocity behavior
  - reconstructed position tracks

## Non-goals
- Real-time detection
- Operational deployment
- Production or safety-critical use
- Commercial services or products

## Data Sources
- Publicly available MARSIM dataset
- No proprietary, confidential, or employer-owned data is used

## Disclaimer
This project is developed independently and outside of any employment activities.

All opinions, implementations, and conclusions expressed here are solely those of the author and do not represent any employer, past or present.

This repository is not affiliated with, sponsored by, or endorsed by any organization.

No part of this work is intended to replace certified GNSS receivers, navigation systems, or safety-critical monitoring solutions.

## License
MIT License

This project is released under the MIT License. The intended use is research and educational purposes.
