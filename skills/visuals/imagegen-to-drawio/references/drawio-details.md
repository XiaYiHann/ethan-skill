# draw.io implementation notes

## Native objects and embedded images

An uncompressed `.drawio` file can use `mxfile > diagram > mxGraphModel` XML. The root cell is commonly `0` and the default layer `1`. Write XML attributes with an XML library so `&`, quotes, and angle brackets in labels remain valid. Reuse an existing diagram structure when possible.

For a PNG image cell, draw.io accepts an embedded style value in this form:

```text
shape=image;imageAspect=1;aspect=fixed;image=data:image/png,BASE64_PAYLOAD;
```

Avoid inserting the usual `data:image/png;base64,...` string directly into a semicolon-delimited cell style: the semicolon can split the value. Ordinary SVG and HTML data URLs use the standard `;base64` form. If the editor API inserts images for you, prefer that API and verify the rendered result.

Preserve each image's aspect ratio. A transparent square canvas may contain a much smaller visible icon; align using the nontransparent bounds rather than equalizing canvas rectangles. Do not stretch a square icon to fill a wide card.

Modules may be parent cells with child cells positioned relative to them. Connector cells should have actual `source` and `target` references so they stay attached when a module moves.

For a module-level raster plate, group its image, native labels and any transparent border anchors under one movable module. Keep anchor geometry aligned to the actual card borders in the image, accounting for transparent padding. Bind connectors to the module or its anchor children; moving the group must move the image, labels and ports together. The plate can be fixed within that group without locking the group itself. Its internal graphics remain raster.

## Centered orthogonal connectors

For a right-to-left connection, start with `(exitX, exitY)=(1, 0.5)` and `(entryX, entryY)=(0, 0.5)`. For a bottom-to-top connection, use `(0.5, 1)` and `(0.5, 0)`. Adapt these midpoint ports for other sides, then inspect the rendered endpoints because shape-perimeter adjustments can shift them.

Convert nested module positions into one coordinate system before calculating a route. Convert waypoints back into the connector's parent coordinates when writing them. Between stacked rows, place a horizontal run near `y_mid=(upper_bottom+lower_top)/2`; between side-by-side modules, place a vertical run near `x_mid=(left_right+right_left)/2`. These are gap midlines, not routes through cards or labels.

For a manual route, `edgeStyle=none;rounded=0;curved=0;` with a few waypoints can be sufficient. Remove stale waypoints for a direct connection. Automatic orthogonal routing also needs visual inspection; a style name does not guarantee centered turns. Adjacent path points should satisfy `abs(Δx)≤ε` or `abs(Δy)≤ε`, allowing only numerical tolerance, and the rendered path should stay clear of content.

## Meaning, type, and final scale

Connectors represent data flow, control flow, or feedback. A failed candidate does not necessarily mean the whole method rejects; parallel checks must not become a false sequence. Resolve these relationships from the source before drawing the route.

Estimate the final text size before export. If the canvas is `W` units wide, text size is `f`, and the figure is placed at `w` inches wide, then:

```text
final_font_pt ≈ f × 72 × w / W
```

For example, `W=1900`, `f=44`, and `w=5.5` give about `9.2 pt`. This is a planning estimate; inspect the exported figure in its actual context. Do not treat an example font size as a venue rule.

A requested font may be substituted during export. On Linux, for example, Times New Roman may resolve to Tinos. Check the resolved font file before rendering and inspect the exported PDF's embedded font names afterward. Such substitution does not satisfy an exact Times New Roman requirement. Reuse a legitimately available font where possible; if it is missing, report the limitation instead of silently substituting. After a font change, recheck label widths, mathematical glyphs, and the figure at its manuscript display size.

When the requested font lacks Unicode modifier letters or subscript glyphs, use native editable subscript/superscript formatting and matching SVG text spans rather than allowing fallback glyphs. Check glyph coverage as well as the family name.

## Equations and symbol fidelity

Use the manuscript TeX or an author-approved expression as the source of truth. The ImageGen reference supplies placement and style, not equation text. Compare every expression with its source before placing it in the diagram.

Keep formulas in their own text or math objects so they do not inherit bold card-title styling. Use ordinary math weight unless the source specifies emphasis; distinguish italic variables from upright operators and text labels.

Check which base symbol receives each accent, as well as subscripts, superscripts, transposes, parentheses, and minus signs. For example, `\hat v_i` and `\hat\pi_i` are different expressions. Do not draw an accent as an unattached decorative line. If using Unicode combining accents, inspect the exported result with the actual font because their position can change under font substitution.

Compare the equation in the editor and in the exported figure at the intended display size. If native text cannot render one expression reliably, use a separate vector equation object and state that its contents are not text-editable. Keep the rest of the diagram editable.

## Editor validation and export

Use a draw.io tool when available. With browser automation, import the `.drawio` file into diagrams.net and inspect the current editor instance; internal selectors and sidebar paths are not stable APIs. Validate the actual file the user will open. A preview in one browser does not prove that another environment loaded the latest version.

Large embedded images can make the XML too large for a URL-based import such as `#create`. Deliver the `.drawio` file for opening or importing instead. Do not upload user assets to a public hosting service just to obtain a preview.

If the user asks to place the figure in LaTeX and a draw.io PDF with editor metadata fails to embed, preserve the original PDF. Copy only its rendered pages into a clean PDF with an available PDF library, verify page size and appearance, and use that copy for manuscript inclusion. This is a recovery step for a demonstrated issue, not a routine export step.
