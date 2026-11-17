# Hybrid Figure 1 assets

`candidate-b-v2-best.png` is the unaltered Image2 refinement of candidate 2. Original three candidates and prompts remain in `../fig1-candidates/`. They are comparisons, not scientific truth: generation introduced misplaced coupling labels and one duplicated/misspelled output in candidate3. The editable first slide corrects these explicitly; the second slide preserves the raw visual reference.

Run `scripts/phase8d-build-fig1-hybrid.py` with Python, python-pptx and Pillow. It crops the rich generated domain illustrations, reconstructs all major card frames, coupling arrows, scenario-tree connections, labels and objective as native PowerPoint objects, and records the source/crop coordinates in `asset-manifest.json`. The current observation panels and soil anchor labels are native editable overlays. No original candidate PNG is edited.

The formal PDF contains only the editable figure. The PPTX and paired-slide-render.pdf retain the reference as page 2; reference-slide.png is that raw comparison. No manuscript body has been recompiled or changed in this round.
