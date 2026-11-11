# Dataset sources and attribution

`python -m scripts.prepare_training_data` downloads the public dataset files used by the detector fine-tuning workflow. The raw data and prepared copies are excluded from Git because they are derived datasets; keep each source's license and attribution when sharing copies.

## Road Objects Detection Dataset

- Source: [SobanHM/Road-Objects-Detection-Dataset](https://huggingface.co/datasets/SobanHM/Road-Objects-Detection-Dataset)
- License stated on the dataset card: CC BY 4.0
- Dataset card reports 1,309 images across train, validation, and test splits.
- Useful labels: bike, bus, car, person, traffic signal, truck.
- Citation: Soban Hussain, *Road Object Detection Dataset (YOLOv8)*, Hugging Face, 2026.

## Road Traffic

- Source: [LibreYOLO/road-traffic](https://huggingface.co/datasets/LibreYOLO/road-traffic)
- License stated on the dataset card: CC BY 4.0; the card also asks users to check original-source terms.
- 814 images across train, validation, and test splits, with 12 labels.
- Useful labels: bicycle, bus, motorcycle, taxi, vehicle. Unused classes are excluded from the merged labels.
- Citation: Ciaglia et al., *Roboflow 100: A Rich Multi-Domain Object Detection Benchmark*, 2022, arXiv:2211.13523.

The preparation script remaps labels to matching COCO category IDs and discards unrelated classes. The source datasets have different capture domains and limited coverage; their use here supports a compact classroom fine-tuning run, not a claim of benchmark accuracy or safety certification.

The prepared merged split used for the current checkpoint contains 1,129 training images, 352 validation images, and 229 held-out test images (1,710 total).

## Optional anonymized mixed-traffic demo video

The [Visaitech Mixed-Traffic Vehicle Detection dataset](https://huggingface.co/datasets/visaitech/vehicle-mixed-traffic-detection) is available under CC BY 4.0 and includes anonymized South Asian dashcam clips. Its 203-clip archive totals about 12 GB. Video files are omitted from this repository; a local copy of clip 040 was used during development. Keep the attribution in `sample_videos/README.md` if copying or redistributing that clip. The dataset card notes that playback timing varies between clips.
