# Model placement (two separate models)

## Model 1 — ResNet18 (current app default)

1. Put weights here:

```
models/model.pth
```

2. `.env`:

```
MODEL_PATH=./models/model.pth
```

3. Restart the Flask backend.

Architecture: **ResNet18**, 4 classes, `state_dict` only.  
Preprocess: `Resize(224)` → `Normalize([0.5]*3, [0.5]*3)`.

Class order:

- Mild Impairment  
- Moderate Impairment  
- No Impairment  
- Very Mild Impairment  

---

## Model 2 — EfficientNet-B0 (Alzheimer CT scan dataset)

Trained separately (`train_model2_local.py` / `train_model2_ct.ipynb`) on the **Alzheimer CT scan** 4-class dataset.  
**Does not replace Model 1.**  
Modality name used in this project: **CT scan** only.

1. Put weights here:

```
models/model2_ct.pth
```

Optional meta file:

```
models/model2_ct_meta.json
```

2. Model 2 checkpoint is a **dict** with:

- `architecture`: `"efficientnet_b0"`
- `state_dict`
- `class_names`, `normalize_mean`, `normalize_std`, etc.

3. **Not loaded by the current `predictor.py` yet** (that loader only supports ResNet18 + `model.pth`).  
   To use Model 2 in the app (side-by-side or switchable), the backend needs a dual-model update.

---

## Folder layout

```
models/
  model.pth           # Model 1 — keep this
  model2_ct.pth       # Model 2 — train via train_model2_ct.ipynb
  model2_ct_meta.json # optional metadata
```

If `model.pth` is missing or incompatible, prediction returns `model_unavailable`.
