---
name: imagegen-to-drawio
description: Create or refine editable draw.io framework diagrams from per-module text-free ImageGen artwork with native labels and bound connectors. Use native objects when internal graphics must be editable, or a whole-figure background when requested. For raster-only images or standalone icons, use image generation directly.
---

# ImageGen to draw.io

Create a source-faithful, editable framework diagram with the requested composition and connector placement completed. Plan the global layout in draw.io and generate the artwork at module level. The supplied material determines wording, equations and relationships; visual references guide style and composition.

## Choose the editing contract

- **Module hybrid mode (default for a new figure):** generate one independent text-free background for each distinct module, containing its illustrations, optional card backing and blank label regions. Read [module-background.md](references/module-background.md). Assemble the plates, native labels/equations and bound semantic connectors in draw.io. Modules move as groups; artwork inside each plate remains raster. This branch requires module-plate generation, without mandatory whole-figure reference generation, separate standalone icons or native card reconstruction.
- **Object mode:** use when internal card geometry, icons or other graphics must be separately editable or replaceable. Follow the object workflow below. Movable modules and bound connectors are also supported by module hybrid mode and alone do not require object mode.
- **Whole-figure hybrid mode:** use when the user explicitly requests a single full-composition background, or when preserving an existing diagram with that editing contract. Read [hybrid-background.md](references/hybrid-background.md). The locked whole-figure plate fixes the graphics and any baked-in arrows; native text remains editable.
- Explicit user preferences override defaults. Preserve an existing diagram's editing contract unless conversion is requested. A labels-only repair keeps its existing assets and topology.

All modes preserve source meaning and requested output dimensions. State the editing boundary: module hybrid supports movable modules, whole-figure hybrid fixes the graphical composition, and raster artwork in either mode has no editable internal strokes.

A labels/equations-only correction to an existing `.drawio` that preserves all graphics and topology uses a repair branch: inspect the file, patch native text, verify the corrected expressions and unchanged geometry/bound connectors, then re-export. Reuse existing assets and provenance; new asset generation does not apply to this branch. New figures, redraws and changed graphics follow the selected mode's generation branch.

## Object mode: required execution order

Choose the reference step from the actual request:

- **New figure:** generate the composition reference with ImageGen. This is a required step, not an optional optimization.
- **Refine an existing figure or redraw using it as the reference:** inspect that figure and use it directly as the composition reference. Preserve the user's chosen base and make the requested changes; generate a new composition reference only if the user requests one.

Then **generate standalone icons with ImageGen → inspect the assets → assemble native draw.io objects → verify the layout and connectors.** Standalone icon generation remains required; old icons may guide the prompts but do not replace it.

Begin assembly only after the selected reference and every required standalone icon exist as inspected files. Record whether the reference was generated or supplied, its path, all generation prompts and returned asset paths, and the icon-to-module mapping. If a required ImageGen step is unavailable or fails, report the blocked stage and retain partial assets; do not substitute placeholders or claim a completed diagram. When resuming the same task, retain its already generated and inspected assets.

## Understand the source

Read the paper, method description, or existing figure. Identify the inputs, stages, outputs, branches, and meaning of each connector. Ask one focused question only when a missing answer changes the structure. Preserve actual order, parallelism, loops, and failure paths; visual symmetry must not change the method.

Follow the user's chosen language, style, and target dimensions. Otherwise use a white background, restrained colors, consistent line icons, and short labels. Plan for the final display width so text remains readable without extreme downscaling.

For new academic framework figures, plan a compact landscape rectangular composition. Set canvas dimensions, module positions, alignment, gaps and outer margins before generating module artwork or a reference. Each module's own aspect ratio follows its content and planned placement. For refinements, preserve the composition except where requested changes require adjustment. The content itself must form the requested rectangular layout; an empty rectangular page is insufficient. Carry connector placement into the plan and inspect final content bounds. Add an enclosing border only when requested or needed to express a real system boundary.

For academic figures, default to **Times New Roman** (including requests phrased as “new times roman”) unless they explicitly choose another font. Carry the font choice through the composition prompt, every editable label and equation, and exported previews/PDFs. Verify the actual exported font; a Times New Roman name in the XML alone is insufficient. Do not silently replace it with Arimo, Arial, Tinos, or another family. If the exact font is unavailable, state that limitation and keep the requested family in the editable source; distinguish any fallback preview from a verified Times New Roman export.

### Compact icon-driven overview standard (all modes)

- **Reduce unnecessary height and text.** For a genuine forward chain, prefer one main horizontal row with compact lower return paths. Group inputs into meaningful icon sets, retaining short labels that identify their roles. Move long tuples, exhaustive check lists and explanatory sentences to a caption or nearby definition when they are not needed to interpret the overview. Keep essential equations, conditions and distinctions visible. Preserve real parallelism and the user's accepted layout; choose aspect ratio from content and final placement rather than imposing 3:1. Reorganize before reducing the planned readable font size.
- **Give feedback a visual mechanism.** When the source includes a feedback gate, depict what it returns or limits with an icon and a short label. For example, a locked reply and budget gauge can express sanitised, capped feedback. Keep exact limits visible where the reader needs them, in the diagram or caption. A formula-only feedback box is insufficient for an icon-driven overview; an unlabeled generic loop is also ambiguous. Do not add feedback where the source has none.
- **Match record icons and routes to the system.** An append-only audit ledger can use a record book or registry with a verification mark; linked blocks are appropriate only when the source actually uses blockchain. The icon must not imply consensus, encryption or approval that the source does not establish. Reserve inter-card gaps and distinct return ports before drawing arrows. Keep the main flow direct and return paths outside cards, distinguish admitted results from refusals, and omit isolated symbols or repeated annotations unless they clarify the carried object. Apply the connector-routing rules below.

Author-required visible fields, formulas and conditions remain in the figure; reduce other detail or reorganize the layout instead of relocating them. At final display width, verify that icons and short labels explain each module, feedback remains recognisable, and arrows meet their intended borders without crossing labels or obscuring branch distinctions. For a density-driven revision, compare placed height, label count and resolved font size with the previous figure. These measurements support visual review; they are not universal acceptance thresholds. Synchronize caption/description when detail moves out of the diagram.

## Object mode 1: Establish the composition reference

For a new figure, call ImageGen to generate the composition reference. Specify the modules, rectangular layout and aspect ratio, essential labels, and directed relationships in the prompt. Inspect the generated image and retain it with its prompt before proceeding.

For refinement of an existing figure or a redraw guided by it, inspect and retain that figure as the reference. Derive the requested changes from it rather than forcing a new ImageGen composition. Supplied style examples for a new figure do not remove that new figure's reference-generation step.

Use the reference for composition and visual style. Rebuild labels, equations, and connectors from the source material. Regenerate an ImageGen-produced reference only when its structure would mislead a reader; minor typography can be corrected in the editable diagram. Continue through the workflow unless the user requests staged review.

## Object mode 2: Generate standalone icons

Map each distinct icon's meaning to a filename and the modules that use it. Call ImageGen separately for each distinct icon, using the selected composition reference to keep the visual language consistent. Repeated roles may share an icon generated in this task:

- One subject on a square canvas, with no words, labels, cards, or surrounding frame.
- Transparent background when supported, with safe space around the visible subject.
- Consistent stroke weight, palette, corner treatment, and visual density.
- A shape that communicates the module's role rather than a generic repeated checklist symbol.

Inspect each generated asset for transparency, clipping, and style consistency. If genuine transparency is unavailable, use a background compatible with the diagram and describe it accurately. Generate icons as independent subjects; cropping the composition reference does not satisfy this stage. Proceed only when every icon in the mapping has an inspected standalone asset.

## Object mode 3: Build the editable draw.io diagram

Check for an existing editable `.drawio` file and revise it when suitable, unless the user requests a new diagram. Otherwise, use an available draw.io tool or write native `.drawio` XML, then open it in the editor. Read [drawio-details.md](references/drawio-details.md) before assembling the diagram; it covers embedded images, connector geometry, font scaling, and equation fidelity.

- Build cards, labels, groups, backgrounds, and connectors as native objects. Embed icons as separate image objects so the file works offline.
- Keep labels editable, modules movable, and connectors bound to real source and target cells. Do not use the flattened reference image as the diagram.
- Preserve icon aspect ratios and align the visible subject, not only its image canvas. Keep labels separate from icons.
- Group objects by logical module. Connectors must express the source method and avoid crossing labels.
- Treat embedded PNG icons as replaceable objects; their internal strokes are not editable vector paths.

### Connector routing

Use these defaults unless the user chooses another style:

- Attach endpoints to the midpoint of the relevant side of each module. Center routes within the gap between those modules, not within the whole canvas.
- Use horizontal and vertical segments. Connect aligned modules directly; otherwise use the fewest useful right-angle turns.
- Adjust nearby modules before adding routing complexity. Keep compact multirow layouts when they express the method clearly.
- A true branch may share a short lead from its source before splitting. Keep distinct sources distinguishable, and place connector labels beside their own segments.

## Object mode: verify and deliver

Inspect the diagram in draw.io: icons display, labels and equations are legible, connectors point in the correct direction, and objects do not overlap. Check every connector endpoint and turn against the routing rules. Edit one label and move one module to confirm that the diagram stays editable and connectors follow; restore the final layout afterward.

Export a preview and inspect it at the intended display size. Check mathematical accents, indices, and font weight against the source. XML parsing alone does not establish visual or editing quality.

If editor access is unavailable, deliver the XML and assets with a clear note that editor validation remains outstanding. A missing editor tool does not require regenerating the image assets.

Deliver the selected reference image, generated standalone icons, editable `.drawio` file, rendered preview, and a short record of reference provenance, generation prompts, returned asset paths, icon mapping, and validation results. Create a ZIP, export a paper-ready PDF, or insert the figure into a manuscript when requested.

Complete only when the required reference step and icon generation are evidenced, the generated icons are embedded as separate objects, the source meaning and requested rectangular composition are correct, every connector follows the agreed routing, and the diagram is legible and editable. Fix layout and connector failures before delivery rather than handing them to the user as manual finishing. Show the preview and file links; identify any outstanding validation explicitly. Do not claim venue compliance or final publication quality from this workflow alone.
