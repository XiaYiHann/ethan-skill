# Per-module text-free backgrounds

Use this default branch for a new framework figure. ImageGen generates independent module artwork; draw.io owns the overall layout, editable text/equations and semantic connectors. Each module moves as a group. Illustrations and any card backing within its PNG remain raster.

## Plan the figure and each module

Read the source and apply the shared source, compactness and routing rules in `SKILL.md`. Establish canvas dimensions, planned display/export width, module positions and connector corridors in draw.io. Then inventory each module's illustrations, exact labels/equations, label hierarchy, blank text-safe rectangles and intended ports. Reserve space for the required readable font before generating artwork.

Each plate represents one logical module, including its visual mechanism and optional card backing. A plate can contain several illustrations when they belong to that module. Do not replace the requested module artwork with an icon-only workflow. A large figure with several modules receives separate plates, rather than one generated image of all its modules. Identical repeated roles may reuse one plate with an explicit module-to-asset mapping.

For a supplied figure or style reference, inspect and retain it. For a new figure, the source-based layout plan is sufficient; a whole-figure ImageGen composition reference is optional when useful or requested, and is never a prerequisite for this branch. The first accepted module plate can serve as a style reference for the others.

## Generate and inspect independent plates

Generate a separate ImageGen asset for each distinct module design. A prompt should specify:

- That module's semantic role and illustrations, its own aspect ratio and intended placement.
- Shared palette, stroke weight, corner treatment and visual density across modules.
- Blank text-safe regions for native overlays; zero text, letters, numerals, pseudo-text, equations or watermarks. Describe the role without requesting its label wording in the image.
- No neighboring modules or cross-module arrows. Keep semantic connectors native in draw.io.
- Transparent exterior when appropriate and supported; otherwise use a background compatible with the planned canvas. Preserve padding and aspect ratio.
- Maximum available native quality and resolution. Use size/quality parameters only when the selected tool exposes them; otherwise request the target in the prompt and record actual returned dimensions.

Inspect each actual file at native resolution and planned display size. Check crisp edges, no blur or unwanted glow, correct source mechanism, usable blank areas, clipping, transparency and consistency with accepted plates. Measure actual label regions and borders instead of assuming generated positions match the prompt. Retain prompts, returned paths and the module-to-asset mapping. Generate or edit only failed or changed modules; keep accepted assets when resuming the task.

Before final assembly, every module must have an inspected plate. A failed required generation step leaves the diagram incomplete; retain partial assets and report the blocked stage. Cropping a whole-figure image into modules does not provide independently generated module plates. Separate standalone icons are unnecessary in this branch.

For a high-resolution export, compare the raster demand of each placed plate with its actual native size. If the diagram canvas is `W` units wide, a plate is placed at `p` units wide, and the export is `E` pixels wide, the plate needs about `p × E / W` native pixels across. Check height as well when relevant. Larger export dimensions or DPI metadata alone do not add native detail. If a plate falls short or looks soft, reduce its placed size when the layout permits, regenerate that module, or report the limit. Do not switch editing modes silently to meet a pixel target; obtain agreement when a change would alter an explicit editing requirement.

## Assemble module groups in draw.io

Read [drawio-details.md](drawio-details.md) before assembly. Embed each original full-resolution PNG as its own image object so the file works offline. Do not flatten the assembled figure into a single background.

Create one movable group per logical module. Place its image, native editable labels/equations and any transparent border anchors as children in local coordinates. Fix the image within the group when needed to preserve alignment, while keeping the group movable. Preserve the image's aspect ratio and align its visible card/illustrations, including any external transparent padding. Use one native cell per independently editable text item; fit hierarchy and line breaks within measured safe areas.

Bind semantic connectors to the module group or its native anchor children at the measured visual borders. Keep routes in the planned inter-module corridors, following the shared orthogonal-routing rules. Do not bind to unrelated free-floating coordinates or route arrows through a PNG's blank label region. Leave the canvas and outer gaps native so modules can be rearranged without regenerating the entire figure.

Module plates are final artwork. Native reconstruction of their cards and extra icon generation are not required. When the user explicitly requires independently editable card geometry or replaceable internal icons, select Object mode instead and follow its generation contract.

## Verify and deliver

Open the saved file in a real draw.io editor. Inspect every module, label/equation, branch, return path and connector endpoint. Edit a native label and move one whole module; confirm that its plate, labels and ports move together and its connectors follow, then restore the final layout. XML parsing alone does not verify editing behavior or visual quality.

Export from the actual model and inspect at the intended display width. For academic figures use the selected font, defaulting to Times New Roman; verify actual rendering and embedded fonts for PDF exports. Check raster detail at the requested export size as well as text readability, mathematical accents/indices and overlap. If editor access is unavailable, deliver the source and assets with the editing-validation gap stated explicitly.

Deliver the individual module PNGs, editable `.drawio`, rendered preview and a concise provenance/validation record including prompts, returned dimensions, asset mapping and any generation reference used. Include PDF, ZIP or manuscript integration when requested. Report that modules move as groups and text/connectors are native; graphical elements within each plate cannot move independently. Show the preview and file links, and identify any outstanding validation without claiming completion or venue compliance from an unverified export.
