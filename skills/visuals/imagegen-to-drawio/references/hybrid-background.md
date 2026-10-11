# Whole-figure text-free background with editable labels

Use this branch when the user explicitly requests a single whole-figure background, or when preserving an existing whole-figure hybrid diagram. New figures otherwise default to [per-module backgrounds](module-background.md). Its output contract is an offline `.drawio` with an embedded, locked PNG background and independently editable native text, plus the original PNG, exported preview and provenance record. Cards, icons and baked-in arrows are not independently editable.

When the user supplies a text-free whole-figure background to preserve, inspect and embed that file directly. Skip generation unless the user requests changes to its graphics. Record supplied provenance and retain the planning, editor and export checks below. The generation section applies when a new or changed background is needed.

## 1. Plan text before generating graphics

Read the source and make a label inventory: exact wording, equations, hierarchy, maximum lines and connector meaning. Establish canvas aspect ratio, target display width, font and text budgets. Define text-safe rectangles in normalized coordinates, including title, each module, connector annotations and footer. Reserve padding for font ascent/descent and likely wording changes. A short-title/two-line-body budget is a useful simple example, not a universal template.

For academic figures retain Times New Roman unless the user selects another family. Since the image has no text, the font applies to overlays and exports, not generated raster glyphs. Use the final-width estimate in drawio-details.md; require a readable target font size before generation.

Apply the compact overview standard in SKILL.md before assigning boxes. Reserve icon space for submitted input groups and any feedback mechanism, with separate short-label areas. Reserve connector corridors and distinct return ports as part of the composition, including enough room for visible arrow stems and heads. Shrinking text later cannot repair an unsuitable tall layout or cards with unusable gaps.

## 2. Generate and inspect the background

**Quality gate:** prioritize the highest available generation quality and fine visual detail. Choose aspect ratio and canvas shape from the content, layout and intended use; resolution must serve that composition. The user's “4K-level” request expresses a quality/detail goal, not a mandatory 16:9 format or a fixed 3840 px acceptance threshold. Request the highest supported native resolution compatible with the chosen composition and maximum quality. Use explicit quality/size parameters only when the selected tool exposes them; otherwise express these requirements in the prompt and report what the tool actually returned.

Inspect the actual PNG dimensions and visual detail before accepting it. At 100% zoom check crisp icon edges, clean curves, consistent strokes, smooth fills, and absence of blur, compression artifacts or malformed details; also inspect at intended display size. Large pixel dimensions alone do not prove fine detail. Retain and embed the original full-resolution file; previews may be smaller. Upscaling or changing DPI metadata does not establish improved native detail. If exposed controls cannot reach the highest supported setting, or visual inspection fails, report the limitation and retain the output as a draft. If the tool hides its quality setting, distinguish the maximum-quality request from verified settings rather than inventing evidence. Follow the imagegen skill's tool/fallback authorization rules when another generation path is needed.

Prompt ImageGen for the entire composition with illustrations and completely empty label areas. Explicitly require zero text, pseudo-text, letters, numerals, equations or watermarks. Specify semantic roles, exact order, rows/columns, approximate card positions, palette, aspect ratio and text-safe rectangles. Do not include the intended label wording in the generation prompt.

For a simple source-verified chain, arrows may be baked in if the user accepts raster arrows. For branches, feedback, uncertainty or topology that may change, generate an arrow-free plate and add native connectors later. Decorative network lines inside an icon are not evidence of method relationships.

Inspect the actual returned file for stray glyphs, correct module count, meaningful icons, arrow directions, usable blank regions and actual dimensions, fine detail and crisp edges at 100% zoom and suitable resolution at target width. Measure the actual label regions; generation coordinates are approximate. Regenerate or edit only when graphics, structure or available space fail. Fix ordinary text spacing in draw.io. Retain the prompt and returned path. Do not crop standalone icons merely to satisfy the separate object-mode procedure.

Check actual connector gaps as well as label boxes. If generated cards leave no usable arrow corridor, revise the spacing or group related modules before another generation attempt; do not repeatedly issue an unchanged request or squeeze connectors into the failed layout. Retain the inspected reference and semantic contract when changing composition. In an audit diagram, check that the ledger and feedback icons express their actual roles rather than an unsupported blockchain or formula-only panel.

## 3. Assemble in draw.io

Read drawio-details.md for embedded-image syntax and exports. Match the canvas to the PNG dimensions or a uniformly scaled equivalent. Embed the PNG so the file opens offline, preserve aspect ratio, and put it on a named Background layer with movement/resizing/editing disabled. Place labels on a separate editable layer.

Use one native text cell per independently editable title, body, annotation or equation. Record cell ID, source wording and measured text-safe box. Transparent fills let the plate show through. Fit text by hierarchy, line breaks and padding; avoid shrinking body text below the planned readable size. Retain formulas as text/math objects when supported, otherwise identify any vector equation exception.

Any native connector needs source/target anchor cells or native modules, with the routing rules from SKILL.md. Do not draw duplicate native arrows over visible raster arrows. Native overlay connectors can follow their anchors, but cannot move raster modules; report this boundary.

For raster cards, place transparent native anchor cells on the measured card borders. Update their positions if the plate changes, and verify the bound routes in the editor; moving an anchor does not move the raster card.

## 4. Verify the actual output

Open the saved model in a real draw.io editor. Check offline embedded-image rendering, all labels, clipping, overlap, source meaning and any native connectors. Edit and move a text cell, restore it, and verify the background stays locked. A hybrid file has no movable graphic module requirement. For native connectors, separately test their anchors and restore.

Export a preview from the draw.io model and inspect it at intended display width. Verify the resolved font and PDF embedded fonts if exporting a PDF. A SVG export may include a compatibility warning switch for non-SVG viewers; remove only that export warning when the real labels are native SVG text, preserving all diagram content and the `.drawio` source. Inspect the repaired preview.

Deliver background PNG, `.drawio`, preview, provenance and validation results. Include PDF/ZIP/manuscript integration only when requested. Report generated image resolution and raster scaling limits, editor-validation gaps and the exact editing boundary. An attractive prototype proves feasibility, not universal superiority or scientific correctness.
