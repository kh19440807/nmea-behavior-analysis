# GNSS Anomaly Detection (Experimental Prototype)

This repository contains an **experimental, non-commercial prototype**
for detecting potential GNSS spoofing behavior from **offline NMEA logs**.

The purpose of this project is **technical exploration and validation only**,
focusing on whether machine-learning-based approaches can distinguish
spoofed vs. unspoofed GNSS behavior when rule-based detection fails.

---

## Key Characteristics

- Offline analysis of recorded NMEA logs
- ML model trained and evaluated on the public **MARSIM maritime spoofing dataset**
- Comparison between:
  - traditional rule-based anomaly detection
  - statistical / ML-based classification
- Visualization of:
  - GNSS signal quality (C/N₀)
  - velocity behavior
  - reconstructed position tracks

---

## Important Notes

- This project **does not provide real-time detection**
- This project **is not a production system**
- This project **is not offered as a service or product**
- No operational or safety guarantees are provided

The implementation and results are intended **solely for research,
learning, and technical discussion**.

---

## Data Sources

- Publicly available MARSIM dataset
- No proprietary, confidential, or employer-owned data is used

---

## Disclaimer

This project is developed **independently and outside of any employment activities**.

All opinions, implementations, and conclusions expressed here are
solely those of the author and **do not represent any employer,
past or present**.

This repository is **not affiliated with, sponsored by,
or endorsed by any organization**.

---

## License

MIT License (research and educational use only)
